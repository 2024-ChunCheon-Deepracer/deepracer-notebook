import math

# https://github.com/dgnzlz/Capstone_AWS_DeepRacer

REWARD_FOR_FASTEST_TIME = 150
STANDARD_TIME = 12  # seconds (time that is easily done by model)
FASTEST_TIME = 8  # seconds (best time of 1st place on the track)


class Reward:
    def __init__(self, verbose=False):
        self.first_racingpoint_index = 0  # None
        self.verbose = verbose

    def reward_function(self, params):
        # Import package (needed for heading)
        # import math

        ################## HELPER FUNCTIONS ###################

        def get_distance(coor1, coor2):
            return math.sqrt((coor1[0] - coor2[0]) * (coor1[0] - coor2[0]) + (coor1[1] - coor2[1]) * (coor1[1] - coor2[1]))

        def get_radians(coor1, coor2):
            return math.atan2((coor2[1] - coor1[1]), (coor2[0] - coor1[0]))

        def get_degrees(coor1, coor2):
            return math.degrees(get_radians(coor1, coor2))

        def get_diff_radians(angle1, angle2):
            diff = (angle1 - angle2) % (2.0 * math.pi)

            if diff >= math.pi:
                diff -= 2.0 * math.pi

            return diff

        def get_diff_degrees(angle1, angle2):
            return math.degrees(get_diff_radians(angle1, angle2))

        def up_sample(waypoints, factor=20):
            p = waypoints
            n = len(p)

            return [
                [
                    i / factor * p[int((j + 1) % n)][0] + (1 - i / factor) * p[j][0],
                    i / factor * p[int((j + 1) % n)][1] + (1 - i / factor) * p[j][1],
                ]
                for j in range(n)
                for i in range(factor)
            ]

        def get_distance_list(car, waypoints):
            dist_list = []
            min_dist = float("inf")
            min_idx = -1

            for i, waypoint in enumerate(waypoints):
                dist = get_distance(car, waypoint)
                if dist < min_dist:
                    min_dist = dist
                    min_idx = i
                dist_list.append(dist)

            return dist_list, min_dist, min_idx, len(waypoints)

        def detect_bot(params):
            car = [params["x"], params["y"]]

            heading = math.radians(params["heading"])
            track_width = params["track_width"]
            is_reversed = params["is_reversed"]

            objects_location = params["objects_location"]
            objects_left_of_center = params["objects_left_of_center"]

            warned = False
            is_inner = False

            bot_idx = -1
            bot_dist = float("inf")

            for i, location in enumerate(objects_location):
                dist = get_distance(car, location)

                angle = get_radians(car, location)

                diff = abs(get_diff_degrees(heading, angle))

                if dist < track_width and diff < 120:
                    warned = True

                    if dist < bot_dist:
                        bot_idx = i
                        bot_dist = dist

            if warned:
                if is_reversed:
                    if objects_left_of_center[bot_idx] == False:
                        is_inner = True
                else:
                    if objects_left_of_center[bot_idx]:
                        is_inner = True

            return warned, is_inner, bot_dist

        ################## HELPER FUNCTIONS ###################

        def dist_2_points(x1, x2, y1, y2):
            return abs(abs(x1 - x2) ** 2 + abs(y1 - y2) ** 2) ** 0.5

        def closest_2_racing_points_index(racing_coords, car_coords):
            # Calculate all distances to racing points
            distances = []
            for i in range(len(racing_coords)):
                distance = dist_2_points(
                    x1=racing_coords[i][0],
                    x2=car_coords[0],
                    y1=racing_coords[i][1],
                    y2=car_coords[1],
                )
                distances.append(distance)

            # Get index of the closest racing point
            closest_index = distances.index(min(distances))

            # Get index of the second closest racing point
            distances_no_closest = distances.copy()
            distances_no_closest[closest_index] = 999
            second_closest_index = distances_no_closest.index(min(distances_no_closest))

            return [closest_index, second_closest_index]

        def dist_to_racing_line(closest_coords, second_closest_coords, car_coords):
            # Calculate the distances between 2 closest racing points
            a = abs(
                dist_2_points(
                    x1=closest_coords[0],
                    x2=second_closest_coords[0],
                    y1=closest_coords[1],
                    y2=second_closest_coords[1],
                )
            )

            # Distances between car and closest and second closest racing point
            b = abs(
                dist_2_points(
                    x1=car_coords[0],
                    x2=closest_coords[0],
                    y1=car_coords[1],
                    y2=closest_coords[1],
                )
            )
            c = abs(
                dist_2_points(
                    x1=car_coords[0],
                    x2=second_closest_coords[0],
                    y1=car_coords[1],
                    y2=second_closest_coords[1],
                )
            )

            # Calculate distance between car and racing line (goes through 2 closest racing points)
            # try-except in case a=0 (rare bug in DeepRacer)
            try:
                distance = abs(-(a**4) + 2 * (a**2) * (b**2) + 2 * (a**2) * (c**2) - (b**4) + 2 * (b**2) * (c**2) - (c**4)) ** 0.5 / (2 * a)
            except:
                distance = b

            return distance

        # Calculate which one of the closest racing points is the next one and which one the previous one
        def next_prev_racing_point(closest_coords, second_closest_coords, car_coords, heading):
            # Virtually set the car more into the heading direction
            heading_vector = [
                math.cos(math.radians(heading)),
                math.sin(math.radians(heading)),
            ]
            new_car_coords = [
                car_coords[0] + heading_vector[0],
                car_coords[1] + heading_vector[1],
            ]

            # Calculate distance from new car coords to 2 closest racing points
            distance_closest_coords_new = dist_2_points(
                x1=new_car_coords[0],
                x2=closest_coords[0],
                y1=new_car_coords[1],
                y2=closest_coords[1],
            )
            distance_second_closest_coords_new = dist_2_points(
                x1=new_car_coords[0],
                x2=second_closest_coords[0],
                y1=new_car_coords[1],
                y2=second_closest_coords[1],
            )

            if distance_closest_coords_new <= distance_second_closest_coords_new:
                next_point_coords = closest_coords
                prev_point_coords = second_closest_coords
            else:
                next_point_coords = second_closest_coords
                prev_point_coords = closest_coords

            return [next_point_coords, prev_point_coords]

        def racing_direction_diff(closest_coords, second_closest_coords, car_coords, heading):
            # Calculate the direction of the center line based on the closest waypoints
            next_point, prev_point = next_prev_racing_point(closest_coords, second_closest_coords, car_coords, heading)

            # Calculate the direction in radius, arctan2(dy, dx), the result is (-pi, pi) in radians
            track_direction = math.atan2(next_point[1] - prev_point[1], next_point[0] - prev_point[0])

            # Convert to degree
            track_direction = math.degrees(track_direction)

            # Calculate the difference between the track direction and the heading direction of the car
            direction_diff = abs(track_direction - heading)
            if direction_diff > 180:
                direction_diff = 360 - direction_diff

            return direction_diff

        # Gives back indexes that lie between start and end index of a cyclical list
        # (start index is included, end index is not)
        def indexes_cyclical(start, end, array_len):
            if end < start:
                end += array_len

            return [index % array_len for index in range(start, end)]

        # Calculate how long car would take for entire lap, if it continued like it did until now
        def projected_time(first_index, closest_index, step_count, times_list):
            # Calculate how much time has passed since start
            current_actual_time = (step_count - 1) / 15

            # Calculate which indexes were already passed
            indexes_traveled = indexes_cyclical(first_index, closest_index, len(times_list))

            # Calculate how much time should have passed if car would have followed optimals
            current_expected_time = sum([times_list[i] for i in indexes_traveled])

            # Calculate how long one entire lap takes if car follows optimals
            total_expected_time = sum(times_list)

            # Calculate how long car would take for entire lap, if it continued like it did until now
            try:
                projected_time = (current_actual_time / current_expected_time) * total_expected_time
            except:
                projected_time = 9999

            return projected_time

        #################### RACING LINE ######################

        # Optimal racing line for the Spain track
        # Each row: [x,y,speed,timeFromPreviousPoint]
        racing_track = []

        racing_track_ccw = [
            [0.26616, 0.85381, 3.6, 0.06298],
            [0.12388, 1.01323, 3.6, 0.05936],
            [-0.01205, 1.16528, 3.6, 0.05665],
            [-0.17019, 1.34215, 3.6, 0.0659],
            [-0.34347, 1.53629, 3.6, 0.07228],
            [-0.52554, 1.74062, 3.6, 0.07602],
            [-0.71443, 1.95296, 3.44482, 0.0825],
            [-0.90885, 2.17192, 2.94762, 0.09934],
            [-1.1072, 2.3957, 2.61194, 0.11448],
            [-1.30725, 2.62167, 2.35697, 0.12805],
            [-1.51227, 2.84039, 2.1115, 0.14198],
            [-1.72428, 3.0419, 1.92697, 0.15179],
            [-1.9439, 3.21729, 1.75832, 0.15984],
            [-2.16946, 3.3592, 1.58547, 0.16809],
            [-2.39767, 3.46289, 1.53182, 0.16363],
            [-2.6244, 3.52576, 1.53182, 0.1536],
            [-2.84474, 3.54518, 1.53182, 0.1444],
            [-3.05308, 3.52022, 1.53182, 0.13698],
            [-3.24242, 3.44958, 1.53182, 0.13192],
            [-3.40177, 3.33038, 1.53182, 0.12991],
            [-3.51955, 3.16648, 1.77156, 0.11393],
            [-3.59869, 2.97391, 1.94105, 0.10726],
            [-3.63938, 2.76056, 2.15179, 0.10094],
            [-3.64329, 2.53313, 2.42168, 0.09393],
            [-3.61392, 2.29766, 2.8233, 0.08405],
            [-3.55795, 2.06036, 2.46019, 0.0991],
            [-3.48464, 1.82684, 2.46019, 0.09949],
            [-3.40352, 1.59838, 2.46019, 0.09854],
            [-3.32464, 1.37911, 2.46019, 0.09472],
            [-3.2557, 1.15719, 2.46019, 0.09445],
            [-3.20702, 0.92986, 2.46019, 0.0945],
            [-3.1898, 0.69397, 2.76736, 0.08547],
            [-3.19926, 0.45062, 3.07037, 0.07931],
            [-3.23264, 0.20033, 3.46494, 0.07288],
            [-3.28714, -0.05659, 3.6, 0.07295],
            [-3.35956, -0.32014, 3.37792, 0.08091],
            [-3.44573, -0.59028, 2.91905, 0.09713],
            [-3.54026, -0.86546, 2.59218, 0.11225],
            [-3.63723, -1.15193, 2.35065, 0.12866],
            [-3.72433, -1.44141, 2.14827, 0.14072],
            [-3.79256, -1.73483, 1.97368, 0.15264],
            [-3.8326, -2.02973, 1.80248, 0.16511],
            [-3.83612, -2.31931, 1.65761, 0.17471],
            [-3.79801, -2.59342, 1.53258, 0.18057],
            [-3.71821, -2.84126, 1.4, 0.18598],
            [-3.60062, -3.05352, 1.4, 0.17333],
            [-3.45161, -3.22323, 1.4, 0.16132],
            [-3.27831, -3.34434, 1.4, 0.15101],
            [-3.08904, -3.41169, 1.4, 0.1435],
            [-2.89344, -3.41951, 1.4, 0.13983],
            [-2.70575, -3.35741, 1.67454, 0.11806],
            [-2.53379, -3.24572, 1.84548, 0.11111],
            [-2.38214, -3.09044, 2.06736, 0.10499],
            [-2.25372, -2.897, 2.38831, 0.09722],
            [-2.14892, -2.67204, 2.22454, 0.11156],
            [-2.06477, -2.42368, 1.96584, 0.13339],
            [-1.99508, -2.16083, 1.75813, 0.15467],
            [-1.91478, -1.90096, 1.58464, 0.17164],
            [-1.8169, -1.66116, 1.43118, 0.18097],
            [-1.69672, -1.4508, 1.43118, 0.16928],
            [-1.55372, -1.27665, 1.43118, 0.15745],
            [-1.39007, -1.14379, 1.43118, 0.14729],
            [-1.20943, -1.05773, 1.43118, 0.13981],
            [-1.01745, -1.02601, 1.43118, 0.13595],
            [-0.82496, -1.06047, 1.65678, 0.11803],
            [-0.64232, -1.14544, 1.76117, 0.11438],
            [-0.47683, -1.27742, 1.86, 0.1138],
            [-0.33627, -1.45417, 1.97136, 0.11456],
            [-0.22911, -1.67237, 1.94053, 0.12527],
            [-0.16392, -1.92608, 1.76373, 0.14852],
            [-0.14738, -2.20569, 1.61752, 0.17317],
            [-0.18299, -2.4975, 1.45986, 0.20137],
            [-0.17604, -2.7394, 1.45986, 0.16578],
            [-0.13256, -2.95307, 1.45986, 0.14936],
            [-0.05485, -3.13747, 1.45986, 0.13707],
            [0.05513, -3.29088, 1.45986, 0.1293],
            [0.19724, -3.40908, 1.45986, 0.12662],
            [0.37524, -3.47975, 1.87631, 0.10207],
            [0.57497, -3.5157, 2.29979, 0.08824],
            [0.7903, -3.52368, 3.25604, 0.06618],
            [1.01401, -3.51545, 3.6, 0.06218],
            [1.26475, -3.51623, 3.6, 0.06965],
            [1.5151, -3.52539, 2.63762, 0.09498],
            [1.76513, -3.54088, 2.14124, 0.117],
            [2.01496, -3.56065, 1.82881, 0.13703],
            [2.26466, -3.58295, 1.59723, 0.15696],
            [2.49658, -3.60277, 1.42703, 0.16311],
            [2.72242, -3.60876, 1.42703, 0.15831],
            [2.93649, -3.59022, 1.42703, 0.15057],
            [3.13332, -3.54018, 1.42703, 0.14232],
            [3.30681, -3.4541, 1.42703, 0.13572],
            [3.44814, -3.3279, 1.42703, 0.13278],
            [3.54184, -3.15852, 1.58887, 0.12182],
            [3.58709, -2.96008, 1.72382, 0.11807],
            [3.58086, -2.74295, 1.88043, 0.11551],
            [3.52211, -2.51814, 2.06963, 0.11227],
            [3.41355, -2.29638, 2.30672, 0.10704],
            [3.26163, -2.08581, 2.6205, 0.09908],
            [3.0749, -1.89036, 3.09125, 0.08745],
            [2.86274, -1.70953, 3.6, 0.07743],
            [2.63434, -1.53966, 3.6, 0.07907],
            [2.40232, -1.35229, 3.6, 0.08284],
            [2.17661, -1.15662, 3.6, 0.08298],
            [1.95653, -0.95402, 3.6, 0.08309],
            [1.7416, -0.74589, 3.6, 0.08311],
            [1.53158, -0.5338, 3.6, 0.08291],
            [1.32659, -0.31956, 3.6, 0.08236],
            [1.1272, -0.10539, 3.6, 0.08128],
            [0.93441, 0.10593, 3.6, 0.07946],
            [0.74959, 0.31134, 3.6, 0.07676],
            [0.57404, 0.50804, 3.6, 0.07323],
            [0.41697, 0.68453, 3.6, 0.06563],
]

        racing_track_cw = [
            [-3.58984, -0.37244, 1.45365, 0.11995],
            [-3.58212, -0.20115, 1.38131, 0.12413],
            [-3.55204, -0.03341, 1.3, 0.13109],
            [-3.49817, 0.12931, 1.3, 0.13185],
            [-3.41785, 0.28482, 1.3, 0.13464],
            [-3.30644, 0.42948, 1.3, 0.14045],
            [-3.15649, 0.55572, 1.69274, 0.1158],
            [-2.98187, 0.66645, 1.84829, 0.11187],
            [-2.78511, 0.76055, 2.01293, 0.10835],
            [-2.56862, 0.8372, 2.2279, 0.10309],
            [-2.33532, 0.89667, 2.50046, 0.09629],
            [-2.08826, 0.94019, 2.75637, 0.09101],
            [-1.82714, 0.96894, 2.80063, 0.0938],
            [-1.57128, 1.01329, 2.72722, 0.09522],
            [-1.32074, 1.07273, 2.63561, 0.0977],
            [-1.07564, 1.14695, 2.63561, 0.09717],
            [-0.83622, 1.23611, 2.63561, 0.09693],
            [-0.60299, 1.34088, 2.63561, 0.09701],
            [-0.3767, 1.46242, 3.1502, 0.08154],
            [-0.15548, 1.59578, 3.33254, 0.07751],
            [0.06146, 1.73889, 3.07596, 0.08449],
            [0.2748, 1.89, 2.85308, 0.09163],
            [0.50676, 2.04072, 2.6628, 0.10389],
            [0.74241, 2.17843, 2.49142, 0.10955],
            [0.98152, 2.30112, 2.34095, 0.1148],
            [1.22366, 2.40678, 2.20818, 0.11964],
            [1.46817, 2.49348, 2.0801, 0.12472],
            [1.71412, 2.55931, 1.95617, 0.13016],
            [1.96024, 2.60242, 1.81063, 0.138],
            [2.20483, 2.6211, 1.67803, 0.14619],
            [2.44574, 2.61353, 1.55903, 0.1546],
            [2.68019, 2.57786, 1.42898, 0.16596],
            [2.9043, 2.51133, 1.31828, 0.17733],
            [3.11283, 2.41145, 1.31828, 0.17539],
            [3.29893, 2.27617, 1.31828, 0.17453],
            [3.45246, 2.1031, 1.31828, 0.17549],
            [3.55899, 1.892, 1.7082, 0.13842],
            [3.63291, 1.66146, 1.83685, 0.1318],
            [3.67532, 1.41554, 1.98924, 0.12545],
            [3.68769, 1.15784, 2.15397, 0.11977],
            [3.67162, 0.89155, 2.32872, 0.11456],
            [3.62883, 0.61949, 2.45267, 0.11229],
            [3.56002, 0.34423, 2.56264, 0.11072],
            [3.46607, 0.06877, 2.65758, 0.10952],
            [3.34842, -0.20317, 2.75949, 0.10737],
            [3.20975, -0.46756, 2.81855, 0.10592],
            [3.05271, -0.72089, 2.85612, 0.10436],
            [2.87987, -0.96068, 2.8624, 0.10327],
            [2.69353, -1.18535, 2.84781, 0.1025],
            [2.49564, -1.394, 2.78291, 0.10333],
            [2.28773, -1.58598, 2.71787, 0.10412],
            [2.07115, -1.7611, 2.5887, 0.10759],
            [1.84705, -1.91932, 2.46383, 0.11134],
            [1.61616, -2.06006, 2.29915, 0.11761],
            [1.37915, -2.1828, 2.14418, 0.12448],
            [1.13642, -2.28601, 2.14418, 0.12301],
            [0.8884, -2.368, 2.14418, 0.12183],
            [0.63544, -2.42589, 2.14418, 0.12102],
            [0.37814, -2.45614, 2.20131, 0.11769],
            [0.11792, -2.4599, 2.61913, 0.09936],
            [-0.14374, -2.44459, 2.85379, 0.09185],
            [-0.40626, -2.41286, 3.07016, 0.08613],
            [-0.66925, -2.36657, 3.33426, 0.08009],
            [-0.93242, -2.3076, 3.61702, 0.07456],
            [-1.19557, -2.23757, 3.89183, 0.06997],
            [-1.4586, -2.15774, 3.72102, 0.07387],
            [-1.72122, -2.06935, 3.11097, 0.08907],
            [-1.97892, -1.97498, 2.67287, 0.10267],
            [-2.22762, -1.87709, 2.36341, 0.11309],
            [-2.46668, -1.77276, 1.59153, 0.16389],
            [-2.69448, -1.6592, 1.59153, 0.15993],
            [-2.90817, -1.53408, 1.59153, 0.1556],
            [-3.10443, -1.39596, 1.59153, 0.15079],
            [-3.2617, -1.23774, 1.61921, 0.13778],
            [-3.38318, -1.06939, 1.61609, 0.12846],
            [-3.47374, -0.89624, 1.59501, 0.12251],
            [-3.53685, -0.72121, 1.57244, 0.11832],
            [-3.57502, -0.54617, 1.51669, 0.11812],
        ]

        ################## INPUT PARAMETERS ###################

        # Read all input parameters
        # all_wheels_on_track = params["all_wheels_on_track"]
        x = params["x"]
        y = params["y"]
        # distance_from_center = params["distance_from_center"]
        # is_left_of_center = params["is_left_of_center"]
        heading = params["heading"]
        progress = params["progress"]
        steps = params["steps"]
        speed = params["speed"]
        steering_angle = params["steering_angle"]
        track_width = params["track_width"]
        # waypoints = params["waypoints"]
        # closest_waypoints = params["closest_waypoints"]
        is_offtrack = params["is_offtrack"]
        is_reversed = params["is_reversed"]

        # closest_objects = params["closest_objects"]

        ############### OPTIMAL X,Y,SPEED,TIME ################

        # track = racing_track

        if is_reversed:
            track = racing_track_cw
        else:
            track = racing_track_ccw

        # if closest_objects:
        #     warned, is_inner, _ = detect_bot(params)

        #     if warned:
        #         if is_inner:
        #             track = outer_track
        #         else:
        #             track = inner_track

        # Get closest indexes for racing line (and distances to all points on racing line)
        closest_index, second_closest_index = closest_2_racing_points_index(track, [x, y])

        # Get optimal [x, y, speed, time] for closest and second closest index
        optimals = track[closest_index]
        optimals_second = track[second_closest_index]

        # Save first racingpoint of episode for later
        if self.verbose == True:
            self.first_racingpoint_index = 0  # this is just for testing purposes
        if steps == 1:
            self.first_racingpoint_index = closest_index

        ################ REWARD AND PUNISHMENT ################

        ## Define the default reward ##
        reward = 1
        MIN_REWARD = 1e-2

        ## Reward if car goes close to optimal racing line ##
        DISTANCE_MULTIPLE = 3
        dist = dist_to_racing_line(optimals[0:2], optimals_second[0:2], [x, y])
        distance_reward = max(MIN_REWARD, 1 - (dist / (track_width * 0.5)))
        reward += distance_reward * DISTANCE_MULTIPLE

        ## Reward if speed is close to optimal speed ##
        SPEED_DIFF_NO_REWARD = 1
        SPEED_MULTIPLE = 3
        speed_diff = abs(optimals[2] - speed)
        if speed_diff <= SPEED_DIFF_NO_REWARD:
            # we use quadratic punishment (not linear) bc we're not as confident with the optimal speed
            # so, we do not punish small deviations from optimal speed
            speed_reward = (1 - (speed_diff / (SPEED_DIFF_NO_REWARD)) ** 2) ** 2
        else:
            speed_reward = 0
        reward += speed_reward * SPEED_MULTIPLE

        # Reward if less steps
        REWARD_PER_STEP_FOR_FASTEST_TIME = 1.5
        # STANDARD_TIME = 50  # seconds (time that is easily done by model)
        # FASTEST_TIME = 20  # seconds (best time of 1st place on the track)
        times_list = [row[3] for row in track]
        projected_time = projected_time(self.first_racingpoint_index, closest_index, steps, times_list)
        try:
            steps_prediction = projected_time * 15 + 1
            reward_prediction = max(
                MIN_REWARD,
                (-REWARD_PER_STEP_FOR_FASTEST_TIME * (FASTEST_TIME) / (STANDARD_TIME - FASTEST_TIME)) * (steps_prediction - (STANDARD_TIME * 15 + 1)),
            )
            steps_reward = min(REWARD_PER_STEP_FOR_FASTEST_TIME, reward_prediction / steps_prediction)
        except:
            steps_reward = 0
        reward += steps_reward

        # Zero reward if obviously wrong direction (e.g. spin)
        direction_diff = racing_direction_diff(optimals[0:2], optimals_second[0:2], [x, y], heading)
        if direction_diff > 30 or abs(steering_angle) > 20:
            reward = MIN_REWARD
        else:
            reward += 1.1 - (direction_diff / 30)

        # Zero reward of obviously too slow
        speed_diff_zero = optimals[2] - speed
        if speed_diff_zero > 0.5:
            reward = MIN_REWARD

        ## Incentive for finishing the lap in less steps ##
        # should be adapted to track length and other rewards
        # REWARD_FOR_FASTEST_TIME = 300
        # STANDARD_TIME = 50  # seconds (time that is easily done by model)
        # FASTEST_TIME = 20  # seconds (best time of 1st place on the track)
        if progress > 99.5:
            finish_reward = max(
                MIN_REWARD,
                (-REWARD_FOR_FASTEST_TIME / (15 * (STANDARD_TIME - FASTEST_TIME))) * (steps - STANDARD_TIME * 15),
            )
        else:
            finish_reward = 0
        reward += finish_reward

        ## Zero reward if off track ##
        if is_offtrack == True:
            reward = MIN_REWARD

        ####################### VERBOSE #######################
        if self.verbose == True:
            print("Closest index: %i" % closest_index)
            print("Distance to racing line: %f" % dist)
            print("=== Distance reward (w/out multiple): %f ===" % (distance_reward))
            print("Optimal speed: %f" % optimals[2])
            print("Speed difference: %f" % speed_diff)
            print("=== Speed reward (w/out multiple): %f ===" % speed_reward)
            print("Direction difference: %f" % direction_diff)
            print("Predicted time: %f" % projected_time)
            print("=== Steps reward: %f ===" % steps_reward)
            print("=== Finish reward: %f ===" % finish_reward)

        #################### RETURN REWARD ####################

        # Always return a float value
        return float(reward)


reward_object = Reward()  # add parameter verbose=True to get noisy output for testing


def reward_function(params):
    return reward_object.reward_function(params)