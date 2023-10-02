# Automate calibrating Voron TAP probe offset
#
# Copyright (C) 2023 Anonoei <dev@anonoei.com>
#
# This file may be distributed under the terms of the MIT license.
from mcu import MCU_endstop

class AutoTAP:
    def __init__(self, config):
        self.state = None
        self.z_endstop = None
        self.z_homing = None
        self.last_state = False
        self.last_z_offset = 0.0
        self.config = config
        self.printer = config.get_printer()

        self.start = config.getfloat('start', 0.5, minval=0.0)
        self.stop = config.getfloat('stop', -0.5, maxval=0.0)
        self.step = config.getfloat('step', -0.0125, maxval=0.0)
        self.accuracy = config.getint('accuracy', 1000, minval=10)
        self.set_at_end = config.getint('set_at_end', 1, minval=0, maxval=1)
        self.samples = config.getint('samples', 5, minval=1)
        self.probing_speed = config.getfloat('probing_speed', None, above=0.0)
        self.lift_speed = config.getfloat('lift_speed', None, above=0.0)

        self.query_endstops = self.printer.load_object(config, 'query_endstops')
        self.printer.register_event_handler("klippy:connect", self.handle_connect)
        
        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_command('AUTO_TAP',
                                    self.cmd_AUTO_TAP,
                                    desc=self.cmd_AUTO_TAP_help)

    def handle_connect(self):
        for endstop, name in self.query_endstops.endstops:
            if name == 'z':
                # check for virtual endstops
                if not isinstance(endstop, MCU_endstop):
                    raise self.printer.config_error("A virtual endstop for z"
                                                    " is not supported for %s"
                                                    % (self.config.get_name()))
                self.z_endstop = EndstopWrapper(self.config, endstop)

        probe = self.printer.lookup_object('probe', default=None)
        if probe is None:
            raise self.printer.config_error("A probe is needed for %s"
                                            % (self.config.get_name()))
        
        if self.samples is None:
            self.samples = probe.sample_count
        if self.lift_speed is None:
            self.lift_speed = probe.lift_speed

        def _move(self, coord, speed):
            self.printer.lookup_object('toolhead').manual_move(coord, speed)

        def _calc_mean(self, positions):
            count = float(len(positions))
            return [sum([pos[i] for pos in positions]) / count for i in range(3)]
        
        def _endstop_triggered(self):
            print_time = self.printer.lookup_object('toolhead').get_last_move_time()
            result = self.z_endstop.query_endstop(print_time)
            if result == "open":
                return False
            return True

        cmd_AUTO_TAP_help = ("Automatically calibrate Voron TAP's probe offset")
        def cmd_AUTO_TAP(self, gcmd):
            if self.z_homing is None:
                raise gcmd.error("Must home axes first")
            
            start = gcmd.get_float("START", self.start, above=0.0)
            stop = gcmd.get_float("STOP", self.stop, below=0.0)
            step = gcmd.get_float("STEP", self.step, below=0.0)
            set_at_end = gcmd.get_int("SET", self.set_at_end, above=0, below=1)
            accuracy = gcmd.get_int("ACCURACY", self.accuracy, above=10)
            sample_count = gcmd.get_int("SAMPLES", self.samples, minval=1)
            speed = gcmd.get_float("PROBE_SPEED", self.probing_speed, above=0.0)
            lift_speed = gcmd.get_float("LIFT_SPEED", self.lift_speed, above=0.0)

            int_start = int(accuracy*start)
            int_stop = int(accuracy*stop)
            int_step = int(accuracy*step)

            toolhead = self.printer.lookup_object('toolhead')
            pos_max = toolhead.get_axis_maximum()
            pos_min = toolhead.get_axis_minimum()

            mid_x = (pos_max.x - pos_min.x)/2
            mid_y = (pos_max.y - pos_min.y)/2

            samples = []
            self._move([mid_x, mid_y, 10], lift_speed)
            while len(samples) < sample_count:
                for z in range(int_start, int_stop, int_step):
                    self._move([None, None, start], lift_speed)
                    self._move([None, None, z/accuracy], speed)
                    if self._endstop_triggered():
                        samples.append(z/accuracy)
                        break
                else:
                    self.gcode.respond_info(f"Failed to actuate z_endstop after full travel")
                    break
            
            if len(samples) == sample_count:
                z_mean = self._calc_mean(samples)
                z_min = min(samples)
                z_max = max(samples)
                self.gcode.respond_info(f"Auto TAP Results\nMean: {z_mean:.4f} Min: {z_min:.3f} Max: {z_max:.4f}")
                if set_at_end:
                    gcmd_offset = self.gcode.create_gcode_command("SET_GCODE_OFFSET",
                                                        "SET_GCODE_OFFSET",
                                                        {'Z': 0.0})
                    self.gcode_move.cmd_SET_GCODE_OFFSET(gcmd_offset)
                    # set new gcode z offset
                    gcmd_offset = self.gcode.create_gcode_command("SET_GCODE_OFFSET",
                                                                "SET_GCODE_OFFSET",
                                                                {'Z_ADJUST': z_mean})
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