# Automate calibrating Voron TAP probe offset
#
# Copyright (C) 2023 Anonoei <dev@anonoei.com>
#
# This file may be distributed under the terms of the MIT license.
from mcu import MCU_endstop

class TapVersion:
    Name = "None"
    Min = 0.0
    Max = 9.0
    Multiple = 2
    Adder = 0
    def Calculate(self, travel: float):
        return (travel * self.Multiple) + self.Adder

class tap_DEV(TapVersion):
    Name = "DEV"
    Min = 0.0
    Max = 9.0
    Multiple = 2
    Adder = 0

class tap_CL_CNC(TapVersion):
    Name = "CL_CNC"
    Min = 0.1
    Max = 1.0
    Multiple = 2
    Adder = 0

class tap_R8(TapVersion):
    Name = "R8"
    Min = 0.7
    Max = 2.0
    Multiple = 10
    Adder = 1

class tap_R6(TapVersion):
    Name = "R6"
    Min = 0.7
    Max = 2.0
    Multiple = 10
    Adder = 1

class tap_VILTALI_CNC(TapVersion):
    Name = "VILTALI_CNC"
    Min = 0.5
    Max = 1.5
    Multiple = 25
    Adder = 0

class AutoTAP:
    def __init__(self, config):
        self.z_endstop = None
        self.z_homing = None

        self.config = config
        self.printer = config.get_printer()

        self.tap_choices = {
<<<<<<< Updated upstream
            "DEV":    "DEV",
            "CL_CNC": "CL_CNC",
            "R8":     "R8",
            "R6":     "R8",
        }

        self.tap_db = {
            "DEV": {
                "Expected": (0.0, 9.0),
                "Multiple": 2,
            },
            "CL_CNC": {
                "Expected": (0.1, 1.0),
                "Multiple": 2,
            },
            "R8": {
                "Expected": (0.7, 2.0),
                "Multiple": 4,
            },
=======
            "DEV":         tap_DEV,
            "CL_CNC":      tap_CL_CNC,
            "R8":          tap_R8,
            "R6":          tap_R6,
            "VILTALI_CNC": tap_VILTALI_CNC
>>>>>>> Stashed changes
        }

        self.tap_version    = config.getchoice( 'tap_version',    choices=self.tap_choices)

        self.x              = config.getfloat(  'x',              default=None)
        self.y              = config.getfloat(  'y',              default=None)
        self.z              = config.getfloat(  'z',              default=10)
        self.probe_to       = config.getfloat(  'probe_to',       default=-2, maxval=0.0)

        self.set            = config.getboolean('set',            default=True)
        self.settling_probe = config.getboolean('settling_probe', default=True)

        self.stop           = config.getfloat(  'stop',           default=2.0,    minval=0.0)
        self.step           = config.getfloat(  'step',           default=0.005,  minval=0.0)

        self.samples        = config.getint(    'samples',        default=None,   minval=1)
        self.retract_dist   = config.getfloat(  'retract',        default=None,   above=0.0)

        self.probe_speed    = config.getfloat(  'probe_speed',    default=1.0,   above=0.0)
        self.lift_speed     = config.getfloat(  'lift_speed',     default=None,   above=0.0)
        self.travel_speed   = config.getfloat(  'travel_speed',   default=1000.0, above=0.0)

        self.offset = None

        self.gcode_move = self.printer.lookup_object('gcode_move')
        self.printer.register_event_handler("klippy:connect", self.handle_connect)
        self.printer.register_event_handler("homing:home_rails_end", self.handle_home_rails_end)
        
        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_command('AUTO_TAP',
                                    self.cmd_AUTO_TAP,
                                    desc=self.cmd_AUTO_TAP_help)
        self.steppers = {}

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
        if not len(self.steppers.keys()) == 3:
            for rail in rails:
                pos_min, pos_max = rail.get_range()
                pos_center = (pos_max - pos_min)/2
                for stepper in rail.get_steppers():
                    name = stepper._name
                    if name == "stepper_x":
                        self.steppers["x"] = [pos_min, pos_max, pos_center]
                        if self.x is None:
                            self.x = pos_center
                    elif name == "stepper_y":
                        self.steppers["y"] = [pos_min, pos_max, pos_center]
                        if self.y is None:
                            self.y = pos_center
                    elif name == "stepper_z":
                        self.z_homing = rail.position_endstop
                        if self.retract_dist is None:
                            self.retract_dist = rail.homing_retract_dist
                        self.steppers["z"] = [pos_min, pos_max, pos_center]

    cmd_AUTO_TAP_help = ("Automatically calibrate Voron TAP's probe offset")
    def cmd_AUTO_TAP(self, gcmd):
        self.printer.lookup_object('toolhead').wait_moves()
        if len(self.steppers.keys()) < 3:
            raise gcmd.error("Must home axes first")
        
        tap_version = gcmd.get('TAP_VERSION', default=self.tap_version)

        x = gcmd.get_float("X", self.x)
        y = gcmd.get_float("Y", self.y)
        z = gcmd.get_float("Z", self.z)
        probe_to = gcmd.get_float("PROBE_TO", self.probe_to)

        set_at_end = gcmd.get_int("SET", default=self.set, minval=0, maxval=1)
        settling_probe = gcmd.get_int("SETTLING_PROBE", default=self.settling_probe, minval=0, maxval=1)

        stop = gcmd.get_float("STOP", default=self.stop, above=0.0)
        step = gcmd.get_float("STEP", default=self.step, above=0.0)

        sample_count = gcmd.get_int("SAMPLES", default=self.samples, minval=1)
        retract = gcmd.get_float("RETRACT", default=self.retract_dist, above=0.0)

        probe_speed = gcmd.get_float("PROBE_SPEED", default=self.probe_speed, above=0.0)
        lift_speed = gcmd.get_float("LIFT_SPEED", default=self.lift_speed, above=0.0)
        travel_speed = gcmd.get_float("TRAVEL_SPEED", default=self.travel_speed, above=0.0)

        force = gcmd.get_int("FORCE", 0, minval=0, maxval=1)
        
        if isinstance(tap_version, str):
            if not tap_version in self.tap_choices.keys():
                raise gcmd.error(f"TAP_VERSION must be one of {', '.join(self.tap_choices.keys())}")
            tap_version = self.tap_choices[tap_version]

        if not force and self.offset is not None:
            self.gcode.respond_info(f"Auto TAP set z-offset on {tap_version} tap to {self.offset:.3f}")
            self._set_z_offset(self.offset)
            return
        
        tap_version: TapVersion = tap_version()
        
        if tap_version.Name == "DEV":
            multiple = gcmd.get_float("DEV_MULTIPLE")
            adder = gcmd.get_float("DEV_ADDER")
            tap_version.Multiple = multiple
            tap_version.Adder = adder

        self._move([x, y, z], travel_speed) # Move to park position
        self._set_z_offset(0.0) # set z-offset to 0

        steps = []
        probes = []
        measures = []
        travels = []
        self.gcode.respond_info(f"Auto TAP performing {sample_count} samples to calculate z-offset on {tap_version} tap\nProbe Min: {probe_to}, Stop: {stop}, Step: {step}")
        self._home(False, False, True)
        self._move([None, None, stop + retract], lift_speed)
        if settling_probe:
            self._probe(self.z_endstop.mcu_endstop, probe_to, probe_speed)
            self._move([None, None, stop + retract], lift_speed)
        while len(travels) < sample_count:
            result = self._tap(step, stop, probe_to, probe_speed)
            self._move([None, None, stop + retract], lift_speed)
            if result is None:
                raise gcmd.error(f"Failed to de-actuate z_endstop after full travel! Try changing STOP to a value larger than {stop}")
            steps.append(result[0])
            probes.append(result[1])
            measures.append(result[2])
            travels.append(result[3])
            sample = f"Auto TAP sample {len(travels)}\n"
            sample += f"Traveled: {travels[-1]:.4f} from z{probes[-1]:.4f} to {measures[-1]:.4f} on step {steps[-1]}"
            self.gcode.respond_info(sample)
        # Move to park position
        self._move([None, None, z], lift_speed)
        
        if len(travels) > 0:
            probe_mean = self._calc_mean(probes)
            probe_min = min(probes)
            probe_max = max(probes)

            measure_mean = self._calc_mean(measures)
            measure_min = self._calc_mean(measures)
            measure_max = self._calc_mean(measures)


            travel_mean = self._calc_mean(travels)
            travel_min = min(travels)
            travel_max = max(travels)

<<<<<<< Updated upstream
            offset = travel_mean * self.tap_db[tap_version]["Multiple"]
=======
            offset = tap_version.Calculate(travel_mean)
>>>>>>> Stashed changes

            results = "Auto TAP Results\n"
            results += f"Samples: {len(travels)}, Total Steps: {sum(steps)}\n"
            results += f"Probe Mean: {probe_mean:.4f} / Min: {probe_min:.4f} / Max: {probe_max:.4f}\n"
            results += f"Measure Mean: {measure_mean:.4f} / Min: {measure_min:.4f} / Max: {measure_max:.4f}\n"
            results += f"Travel Mean: {travel_mean:.4f} / Min: {travel_min:.4f} / Max: {travel_max:.4f}\n"
            results += f"Calculated z-offset on {tap_version} tap: {offset:.3f}"
            self.gcode.respond_info(results)

            offset_max = self.tap_db[tap_version]["Expected"][1]
            if offset < tap_version.Min or offset > tap_version.Max:
                raise gcmd.error(f"Offset does not match expected result. Expected between {tap_version.Min:.2f}-{tap_version.Max:.2f}, Got: {offset:.3f}")
            
            self.offset = offset
            if set_at_end:
                self._set_z_offset(self.offset)

    def _tap(self, step_size: float, stop: float, probe_min, probe_speed: float): # -> tuple[int, float, float, float]
        probe = self._probe(self.z_endstop.mcu_endstop, probe_min, probe_speed)[2] # Moves until TAP actuates
        steps = int((abs(probe) + stop) / step_size)
        for step in range(0, steps):
            z_pos = probe + (step * step_size) # checking z-position
            self._move([None, None, z_pos], probe_speed)
            self.printer.lookup_object('toolhead').wait_moves() # Wait for toolhead to move
            if not self._endstop_triggered():
                travel = abs(probe - z_pos)
                return(step, probe, z_pos, travel)
        return None

    def _move(self, coord, speed):
        self.printer.lookup_object('toolhead').manual_move(coord, speed)

    def _probe(self, mcu_endstop, min_z: float, speed: float): # -> list[float, float, float]
        toolhead = self.printer.lookup_object('toolhead')
        pos = toolhead.get_position()
        pos[2] = min_z
        homing = self.printer.lookup_object('homing')
        return homing.probing_move(mcu_endstop, pos, speed)
    
    def _home(self, x=True, y=True, z=True):
        command = ["G28"]
        if x:
            command[-1] += " X0"
        if y:
            command[-1] += " Y0"
        if z:
            command[-1] += " Z0"
        self.gcode._process_commands(command, False)
        self.printer.lookup_object('toolhead').wait_moves()
    
    def _endstop_triggered(self):
        print_time = self.printer.lookup_object('toolhead').get_last_move_time()
        result = self.z_endstop.query_endstop(print_time)
        if result == 0:
            return False
        return True

    def _calc_mean(self, positions):
        count = float(len(positions))
        return sum(positions) / count

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