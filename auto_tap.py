# Automate calibrating Voron TAP probe offset
#
# Copyright (C) 2023 Anonoei <dev@anonoei.com>
#
# This file may be distributed under the terms of the MIT license.
from mcu import MCU_endstop

class AutoTAP:
    def __init__(self, config):
        self.z_endstop = None
        self.z_homing = None

        self.config = config
        self.printer = config.get_printer()

        self.x = config.getfloat('x', 150)
        self.y = config.getfloat('y', 150)
        self.z = config.getfloat('z', 10)
        self.settling_probe = config.getint('settling_probe', 1, minval=0, maxval=1)
        self.stop = config.getfloat('stop', 1.0, minval=0.0)
        self.step = config.getfloat('step', 0.005, minval=0.0)
        self.set = config.getint('set', 1, minval=0, maxval=1)
        self.samples = config.getint('samples', None, minval=1)
        self.retract_dist = config.getfloat('retract', None, above=0.)
        self.probe_speed = config.getfloat('probe_speed', None, above=0.0)
        self.lift_speed = config.getfloat('lift_speed', None, above=0.0)
        self.travel_speed = config.getfloat('travel_speed', 1000.0, above=0.0)

        self.offset = None

        self.gcode_move = self.printer.lookup_object('gcode_move')
        self.printer.register_event_handler("klippy:connect", self.handle_connect)
        self.printer.register_event_handler("homing:home_rails_end", self.handle_home_rails_end)
        
        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_command('AUTO_TAP',
                                    self.cmd_AUTO_TAP,
                                    desc=self.cmd_AUTO_TAP_help)

    def handle_connect(self):
        for endstop, name in self.printer.load_object(self.config, 'query_endstops').endstops:
            if name == 'z':
                self.z_endstop = EndstopWrapper(self.config, endstop)

        probe = self.printer.lookup_object('probe', default=None)
        if probe is None:
            raise self.printer.config_error("A probe is needed for %s"
                                            % (self.config.get_name()))
        
        if self.samples is None:
            self.samples = probe.sample_count
        if self.lift_speed is None:
            self.lift_speed = probe.lift_speed

    def handle_home_rails_end(self, homing_state, rails):
        # get z homing position
        for rail in rails:
            if rail.get_steppers()[0].is_active_axis('z'):
                # get homing settings from z rail
                self.z_homing = rail.position_endstop
                if self.probe_speed is None:
                    self.probe_speed = rail.homing_speed
                if self.retract_dist is None:
                    self.retract_dist = rail.homing_retract_dist

    cmd_AUTO_TAP_help = ("Automatically calibrate Voron TAP's probe offset")
    def cmd_AUTO_TAP(self, gcmd):
        if self.z_homing is None:
            raise gcmd.error("Must home axes first")
        
        x = gcmd.get_float("X", self.x)
        y = gcmd.get_float("Y", self.y)
        z = gcmd.get_float("Z", self.z)
        settling_probe = gcmd.get_int("SETTLING_PROBE", self.settling_probe, minval=0, maxval=1)
        stop = gcmd.get_float("STOP", self.stop, above=0.0)
        step = gcmd.get_float("STEP", self.step, above=0.0)
        set_at_end = gcmd.get_int("SET", self.set, minval=0, maxval=1)
        sample_count = gcmd.get_int("SAMPLES", self.samples, minval=1)
        retract = gcmd.get_float("RETRACT", self.retract_dist, above=0.0)
        probe_speed = gcmd.get_float("PROBE_SPEED", self.probe_speed, above=0.0)
        lift_speed = gcmd.get_float("LIFT_SPEED", self.lift_speed, above=0.0)
        travel_speed = gcmd.get_float("TRAVEL_SPEED", self.travel_speed, above=0.0)

        force = gcmd.get_int("FORCE", 0, minval=0, maxval=1)

        if not force and self.offset is not None:
            self.gcode.respond_info(f"Auto TAP set z-offset to {self.offset:.3f}")
            self._set_z_offset(self.offset)
            return

        self._move([x, y, z], travel_speed) # Move to probe position
        self._set_z_offset(0.0) # reset gcode z offset to 0

        step_count = int(stop / step)
        self.gcode.respond_info(f"Auto TAP performing {sample_count} samples with {step_count} steps\nStop: {stop}, Step: {step}")
        steps = []
        probes = []
        travels = []
        if settling_probe:
            self._probe(self.z_endstop.mcu_endstop, -1, probe_speed)
            self._move([None, None, stop + retract], lift_speed)
        while len(travels) < sample_count:
            start_at = self._probe(self.z_endstop.mcu_endstop, -1, probe_speed)[2]
            #self.gcode.respond_info(f"Starting sample {len(travels) + 1}")
            for i in range(0, step_count, 1):
                z_pos = start_at + (step * i)
                #self.gcode.respond_info(f"Step {i}, moving to {z_pos}")
                self._move([None, None, z_pos], probe_speed)
                self.printer.lookup_object('toolhead').wait_moves()
                if not self._endstop_triggered():
                    steps.append(i)
                    probes.append(start_at)
                    travel = abs(start_at) + abs(z_pos)
                    travels.append(travel)
                    sample = f"Auto TAP sample {len(travels)}\n"
                    sample += f"Traveled: {travel:.4f} from z{start_at:.4f} to {z_pos:.4f} on step {i}"
                    self.gcode.respond_info(sample)
                    self._move([None, None, stop + retract], lift_speed)
                    break
            else:
                self.gcode.respond_info(f"Failed to actuate z_endstop after full travel")
                break
            self._move([None, None, stop + retract], lift_speed)
        # Move to probe position
        self._move([None, None, z], lift_speed)
        
        if len(travels) > 0:
            probe_mean = self._calc_mean(probes)
            probe_min = min(probes)
            probe_max = max(probes)

            step_mean = self._calc_mean(steps)
            step_min = min(steps)
            step_max = max(steps)

            travel_mean = self._calc_mean(travels)
            travel_min = min(travels)
            travel_max = max(travels)

            travel_offset = travel_mean * 2

            results = "Auto TAP Results\n"
            results += f"Samples: {len(travels)}, Total Steps: {sum(steps)}\n"
            results += f"Travel Mean: {travel_mean:.4f} / Min: {travel_min:.4f} / Max: {travel_max:.4f}\n"
            results += f"Probe Mean: {probe_mean:.4f} / Min: {probe_min:.4f} / Max: {probe_max:.4f}\n"
            results += f"Step Mean: {step_mean:.2f} / Min: {step_min} / Max: {step_max}\n"
            results += f"Calculated Z-Offset: {travel_offset:.3f}"
            self.gcode.respond_info(results)
            self.offset = travel_offset
            if set_at_end:
                self._set_z_offset(self.offset)

    def _move(self, coord, speed):
        self.printer.lookup_object('toolhead').manual_move(coord, speed)

    def _probe(self, mcu_endstop, z_position, speed):
        toolhead = self.printer.lookup_object('toolhead')
        pos = toolhead.get_position()
        pos[2] = z_position
        phoming = self.printer.lookup_object('homing')
        curpos = phoming.probing_move(mcu_endstop, pos, speed)
        #self.gcode.respond_info(f"Auto TAP probed {curpos[0]:.3f}, {curpos[1]:.3f}, got z={curpos[2]:.4f}")
        return curpos

    def _calc_mean(self, positions):
        count = float(len(positions))
        return sum(positions) / count
    
    def _endstop_triggered(self):
        print_time = self.printer.lookup_object('toolhead').get_last_move_time()
        result = self.z_endstop.query_endstop(print_time)
        if result == 0:
            return False
        return True

    def _set_z_offset(self, offset):
        gcmd_offset = self.gcode.create_gcode_command("SET_GCODE_OFFSET",
                                                      "SET_GCODE_OFFSET",
                                                      {'Z': offset})
        self.gcode_move.cmd_SET_GCODE_OFFSET(gcmd_offset)


class EndstopWrapper:
    def __init__(self, config, endstop):
        self.mcu_endstop = endstop
        # Wrappers
        self.get_mcu = self.mcu_endstop.get_mcu
        self.add_stepper = self.mcu_endstop.add_stepper
        self.get_steppers = self.mcu_endstop.get_steppers
        self.home_start = self.mcu_endstop.home_start
        self.home_wait = self.mcu_endstop.home_wait
        self.query_endstop = self.mcu_endstop.query_endstop

def load_config(config):
    return AutoTAP(config)