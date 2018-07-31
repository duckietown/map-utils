import sys
import random
import map_gen_beta_2
import argparse
import re
import math
#""
a = random.randint(0,10000)
print(a)
random.seed(a)
"""
random.seed(5178)
"""

# this dictionary's keys are the connections of a
# node in the map, the values are the corresponding tiles
TILE_DICTIONARY = {
    frozenset([("N", 0), ("E", 0), ("S", 0), ("W", 0)]): "empty",

    frozenset([("N", 1), ("E", 1), ("S", 0), ("W", 0)]): "curve_right/W",
    frozenset([("N", 1), ("E", 0), ("S", 1), ("W", 0)]): "straight/N",
    frozenset([("N", 1), ("E", 0), ("S", 0), ("W", 1)]): "curve_left/E",
    frozenset([("N", 0), ("E", 1), ("S", 1), ("W", 0)]): "curve_right/N",
    frozenset([("N", 0), ("E", 1), ("S", 0), ("W", 1)]): "straight/W",
    frozenset([("N", 0), ("E", 0), ("S", 1), ("W", 1)]): "curve_left/N",

    frozenset([("N", 1), ("E", 1), ("S", 1), ("W", 0)]): "3way_right/N",
    frozenset([("N", 1), ("E", 1), ("S", 0), ("W", 1)]): "3way_right/W",
    frozenset([("N", 1), ("E", 0), ("S", 1), ("W", 1)]): "3way_left/N",
    frozenset([("N", 0), ("E", 1), ("S", 1), ("W", 1)]): "3way_right/E",

    frozenset([("N", 1), ("E", 1), ("S", 1), ("W", 1)]): "4way"
}
EMPTY_TYPES = ["asphalt", "grass", "floor"]

# the file onto which we write the output
f = open("output.yaml", "w+")

# generates grid, writes it to file,
# generates objects, writes them to file
def main(height, width, has_intersections, map_density, has_border, obj_density, clear_road):
    f.write("tiles:\r\n")
    tile_grid = gen_tile_grid(height, width, has_intersections, map_density)
    tile_grid = define_inner_empties(height, width, tile_grid)

    if (has_border):
        tile_grid = add_border(tile_grid, height, width)

    write_map(tile_grid)
    populate(tile_grid, len(tile_grid), len(tile_grid[0]), obj_density, clear_road)
    #print_objects()
    if (NUM_OBJECTS>0):
        write_objects()
    f.close()


#===========================================================================================
#===========================================================================================


def write_map(tile_grid):
    for j in range(0, len(tile_grid)):
        f.write("- [")
        for i in range(0, len(tile_grid[0])):
            if tile_grid[j][i] == "":
                raise ValueError("Undefined tile at coordinates: ({}, {}".format(i, j))
            else:
                f.write(tile_grid[j][i])

            # every element followed by "," unless it is last element
            if (i < len(tile_grid[0]) - 1):
                f.write(",")
                for s in range(0, (14 - len(tile_grid[j][i]))):
                    f.write(" ")
        f.write("]\r\n")
    f.write("\r\n")


def add_border(tile_grid, height, width):
    border_empty = EMPTY_TYPES[random.randint(0, len(EMPTY_TYPES) - 1)]
    new_grid = [["" for x in range(width + 2)] for y in range(height + 2)]
    for j in range(0, len(new_grid)):
        for i in range(0, len(new_grid[0])):
            if ((j == 0) or (j == len(new_grid)-1) or
                (i == 0) or (i == len(new_grid[0]) - 1)
            ):
                new_grid[j][i] = border_empty
            else:
                new_grid[j][i] = tile_grid[j-1][i-1]

    return new_grid



# creates grid that fills all non-manually decided tiles with semi-random tiles
# writes grid to output.yaml
# returns grid, in case needed
def gen_tile_grid(height, width, has_intersections, density):
    tile_grid = [["" for x in range(width)] for y in range(height)]
    try:
        node_map = map_gen_beta_2.create_map(height, width, has_intersections, density)
    except:
        raise ValueError("There was a problem generating the map")

    for j in range(0, height):
        for i in range(0, width):
            tile_grid[j][i] = TILE_DICTIONARY[frozenset(node_map[j][i].connected.items())]

    return tile_grid


# defines all neighbouring empty tiles to be the same type, at random
def define_inner_empties(height, width, tile_grid):
    inner_types = list(EMPTY_TYPES)
    inner_types.remove("floor")
    for j in range(0, height):
        for i in range(0, width):
           if (tile_grid[j][i] == "empty"):
                groups_type = inner_types[random.randint(0, 1)]
                tile_grid = group_empties(tile_grid, height, width, i, j, groups_type)
    return tile_grid

# recursively changes all empty tiles in a neighbouring group to the same type
def group_empties(tile_grid, height, width, i, j, groups_type):
    tile_grid[j][i] = groups_type
    if (j<height-1) and (tile_grid[j+1][i] == "empty"):
        tile_grid = group_empties(tile_grid, height, width, i, j+1, groups_type)
    if (i<width-1) and (tile_grid[j][i+1] == "empty"):
        tile_grid = group_empties(tile_grid, height, width, i+1, j, groups_type)
    return tile_grid


#===========================================================================================
#========================== POPULATE MAP WITH OBJECTS ======================================

# list of objects to be written to file
# element format: ( "kind", x, y, rotation, height, optional )
OBJECT_LIST = []

# list of objects to be used for avoiding object overlap
# element format: ("kind", top-left_x, top-left_y, bottom-right_x, bottom-right_y, tile_x, tile_y)
FILLED_TABLE = []

NUM_OBJECTS = 0

# Dimensions.
# Element format -- type": (z-height, ~radius)
DIMS = {
    "barrier": (0.08, 0.25),
    "cone": (0.08, 0.04),
    "duckie": (0.08, 0.04),   # (pedestrian)
    "duckiebot": (0.1, 0.1),  # (car)
    "tree": (0.25, 0.1),
    "house": (0.5, 0.6),
    "truck": (0.2, 0.2),
    "bus": (0.18, 0.45),
    "building": (0.6, 0.45),
    "sign": (0.18, 0.1)
}

# Which objects are allowed on each type of tile
TILE_OPTIONS = {
    "floor": (
        "barrier",
        "cone",
        "duckie",
        "duckiebot",
        "house",
        "truck",
        "bus",
        "building",
        "sign"
    ),
    "grass": (
        "duckie",
        "tree",
        "house",
        "building",
        "sign"
    ),
    "asphalt": (
        "barrier",
        "cone",
        "duckie",
        "duckiebot",
        "house",
        "truck",
        "bus",
        "building",
        "sign"
    ),
    "straight": (
        "barrier",
        "cone",
        "duckie",
        "duckiebot",
        "bus",
        "truck",
        "sign"
    ),
    "curve": (
        "barrier",
        "cone",
        "duckie",
        "sign"
    ),
}
MISC_SIGNS = [
    "sign_do_not_enter",
    "sign_pedestrian",
    "sign_t_light_ahead",
    "sign_yield"
]

# TODO: make clear roads allow other tiles but only signs
# initialises variables needed for object generation,
# calls place_object(), when appropriate, to do the hard work
# (map is a 2D array of tile strings)
def populate(map, height, width, density, clear_road):
    global NUM_OBJECTS
    global TILE_OPTIONS
    global FILLED_TABLE

    # number of tiles where objects may be placed
    num_valid_tiles = 0
    for d in range(0, height):
        for c in range(0, width):
            if (clear_road):
                condition = ("grass" in map[d][c]) or ("floor" in map[d][c]) or ("asphalt" in map[d][c])
            else:
                condition = ("3way" not in map[d][c]) and ("4way" not in map[d][c])

            if condition:
                num_valid_tiles += 1

    if (density == "any"):
        density = ["empty", "sparse", "medium", "dense"][random.randint(0, 2)]

    if (density == "empty"):
        NUM_OBJECTS = 0
    elif (density == "sparse"):
        NUM_OBJECTS = int(num_valid_tiles * 0.1)
    elif (density == "medium"):
        NUM_OBJECTS = int(num_valid_tiles * 0.2)
    else:  # dense
        NUM_OBJECTS = int(num_valid_tiles * 0.3)


    if (clear_road):
        TILE_OPTIONS["straight"] = ("sign")
        TILE_OPTIONS["curve"] = ("sign")

    # 2D array where each element has a list of objects that may be placed,
    # based on the type of tile at the corresponding coordinates
    poss_table = [[None for x in range(width)] for y in range(height)]
    for j in range(0, height):
        for i in range(0, width):
            sliced_string = re.split("[^A-Za-z0-9]+", map[j][i])

            if (sliced_string[0] == "4way") or (sliced_string[0] == "3way"):
                print(map[j][i])
                print(sliced_string)
                signage(sliced_string, i, j)
                continue
            poss_table[j][i] = TILE_OPTIONS[sliced_string[0]]

    # If the random coordinates are that of a tile on which objects may be placed,
    # place_object() is called.
    # Object will only actually be placed if there is no collision with existing ones.
    num_signs = len(OBJECT_LIST) + 0
    while (len(OBJECT_LIST) < NUM_OBJECTS + num_signs):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)

        if (clear_road):
            condition = ("grass" in map[y][x]) or ("floor" in map[y][x]) or ("asphalt" in map[y][x])
        else:
            condition = ("3way" not in map[y][x]) and ("4way" not in map[y][x])

        if (condition):
            # what can be placed on the current type of tile
            sliced_string = re.split("[^A-Za-z0-9]+", map[y][x])
            curr_options = TILE_OPTIONS[sliced_string[0]]
            object = curr_options[random.randint(0, len(curr_options) - 1)]

            # place it
            place_object(map, object, x, y, sliced_string)



def allowed(map, orig_x, orig_y, obj_x, obj_y, object):
    global FILLED_TABLE

    curr_tile = map[orig_y][orig_x]

    # extremities of object
    top_left_x =     obj_x - DIMS[object][1]
    top_left_y =     obj_y - DIMS[object][1]
    bottom_right_x = obj_x + DIMS[object][1]
    bottom_right_y = obj_y + DIMS[object][1]

    # curves and straights cannot have two non-sign objects;
    # becomes too hard to navigate
    if ("curve" in curr_tile) or ("straight" in curr_tile):
        sign_ctr = 0
        for i in range(0, len(FILLED_TABLE)):
            # if element of FILLED TABLE is in the current tile
            if (orig_x == FILLED_TABLE[i][5]) and (orig_y == FILLED_TABLE[i][6]):
                if (sign_ctr > 1):
                    return False
                elif (object == "sign"):
                    if ("sign" in FILLED_TABLE[i][0]):
                        sign_ctr += 1
                # if there is already a non-sign object, cannot place new object
                elif ("sign" not in FILLED_TABLE[i][0]):
                    return False
        FILLED_TABLE.append((object, top_left_x, top_left_y, bottom_right_x, bottom_right_y, orig_x, orig_y))
        return True

    else:  # grass, asphalt, and floor
        for j in range(0, len(FILLED_TABLE)):
            filled_centre_x = (FILLED_TABLE[j][1] + FILLED_TABLE[j][3]) / 2
            filled_centre_y = (FILLED_TABLE[j][2] + FILLED_TABLE[j][4]) / 2
            filled_element = FILLED_TABLE[j]
            # if there is an overlap of objects;
            # 1st and 2nd clauses see if there is partial overlap
            # 3rd clause tests if new object envelops pre-established object
            if ((((FILLED_TABLE[j][1] < top_left_x and top_left_x < FILLED_TABLE[j][3]) or
                  (FILLED_TABLE[j][1] < bottom_right_x and bottom_right_x < FILLED_TABLE[j][3]))
                 and
                 ((FILLED_TABLE[j][2] < top_left_y and top_left_y < FILLED_TABLE[j][4]) or
                  (FILLED_TABLE[j][2] < bottom_right_y and bottom_right_y < FILLED_TABLE[j][4])))
                 or
                 ((top_left_y < filled_centre_y and filled_centre_y < bottom_right_y) and
                  (top_left_x < filled_centre_x and filled_centre_x < bottom_right_x))

            ):
                return False
        FILLED_TABLE.append((object, top_left_x, top_left_y, bottom_right_x, bottom_right_y, orig_x, orig_y))
        return True


def place_object(map, object, x, y, sliced_string):
    global OBJECT_LIST
    # orig_x and orig_y are the coordinate of the tile;
    # x and y will be used for the object
    orig_x = int(x)
    orig_y = int(y)
    curr_tile = map[y][x]

    # dim_code used for objects that share dimensions (i.e. signs)
    if (object == "sign"):
        dim_code = "sign"
        object = MISC_SIGNS[random.randint(0, len(MISC_SIGNS) - 1)]
    else:
        dim_code = str(object)

    # using equation of a circle: x^2 + y^2 = r^2
    # we calculate the object's position
    if ("curve" in curr_tile):
        if ("left" == sliced_string[1]):
            conversion = {"N": "S", "E": "W", "S": "N", "W": "E"}
            sliced_string[2] = conversion[sliced_string[2]]
        """
        if ("right" == sliced_string[1]):
            conversion = {"N": "S", "E": "W", "S": "N", "W": "E"}
            sliced_string[2] = conversion[sliced_string[2]]
        """

        # signs are always on the edges
        if (dim_code == "sign") or (dim_code == "duckie"):
            angle = [-(math.pi / 2), 0][random.randint(0, 1)]
        else:
            angle = round(random.uniform(-(math.pi / 2), 0), 2)

        if (dim_code == "sign"):
            # TODO: implement "one-way" signs
            r = 1
        else:
            r = [0.25, 0.75][random.randint(0, 1)]

        if ("S" == sliced_string[2]):  # Q2  |_
            angle += math.pi / 2
        elif ("E" == sliced_string[2]):  # Q3 _|
            angle += math.pi
        elif ("N" == sliced_string[2]):  # Q4  --|
            angle += 3 * (math.pi / 2)

        obj_x = round(math.cos(angle) * r, 2)
        obj_y = round(math.sin(angle) * r, 2)
        if ("E" == sliced_string[2]) or ("S" == sliced_string[2]):
            y += 1
        if ("E" == sliced_string[2]) or ("N" == sliced_string[2]):
            x += 1
        # all signs come in pairs; here we calculate where it goes
        sign2_x = x + 0
        sign2_y = y + 0
        x += obj_x
        y -= obj_y

        # convert to degrees
        angle = round(angle * (180 / math.pi), 2)

        # randomize direction object is facing
        rotation = 0
        if ("sign" in object):
            rotation = 270
            # if both signs are safe to place, we place sign 2
            if ((allowed(map, orig_x, orig_y, sign2_x, sign2_y, dim_code)) and
                (allowed(map, orig_x, orig_y, x, y, dim_code))):
                OBJECT_LIST.append((object, sign2_x, sign2_y, angle + 90, DIMS[dim_code][0], False))
            else:
                return
        elif (object == "cone"):
            rotation = round(random.uniform(0, 90))
        elif (object == "duckie"):
            rotation = random.randint(0, 1) * 180
        elif (object == "truck") or (object == "duckiebot"):
            if (r > 0.5):
                rotation = 90
            else:
                angle = 270
        if (allowed(map, orig_x, orig_y, x, y, dim_code)):
            OBJECT_LIST.append((object, x, y, angle + rotation, DIMS[dim_code][0], False))
        else:
            return

    elif ("straight" in curr_tile):

        if (object == "cone"):
            lane = round(random.uniform(0, 1), 2)
        else:
            lane = [0.25, 0.75][random.randint(0, 1)]

        if ("sign" in object):
            lane = round(lane)
            str8_coord = round(random.uniform(0.25, 0.75), 2)
        # for vehicles, overlap into neighbouring tiles is limited to 0.25*radius
        elif (object == "truck") or (object == "bus"):
            str8_coord = round(random.uniform(0.75 * DIMS[object][1], 1 - (0.75 * DIMS[object][1])), 2)
        else:
            str8_coord = round(random.uniform(0, 1), 2)

        # here we enter into a stream of adjustments that must be made
        # the coordinates depending on the kind of object and its direction
        if ("N" in curr_tile) or ("S" in curr_tile):
            obj_y = str8_coord
            obj_x = lane
            if (lane < 0.5):
                rotation = 270
            else:
                rotation = 90
        elif ("E" in curr_tile) or ("W" in curr_tile):
            obj_x = str8_coord
            obj_y = lane
            if (lane < 0.5):
                rotation = 180
            else:
                rotation = 0
        else:
            raise ValueError("unrecognized direction string")

        if (object == "cone"):
            rotation += round(random.uniform(0, 90), 2)
        elif (object == "barrier"):
            rotation += 90

        if (object == "duckie"):
            if ("N" in curr_tile) or ("S" in curr_tile):
                cross_x = [0, 1]
                cross_y = [obj_y]
                cross_rotn = [270, 90]
            else:
                cross_y = [0, 1]
                cross_x = [obj_x]
                cross_rotn = [0, 180]
            if ((allowed(map, orig_x, orig_y, x + cross_x[0],  y + cross_y[0],  dim_code)) and
                (allowed(map, orig_x, orig_y, x + cross_x[-1], y + cross_y[-1], dim_code)) and
                (allowed(map, orig_x, orig_y, x + obj_x,       y + obj_y,       dim_code))
            ):
                OBJECT_LIST.append(("sign_duck_crossing", x + cross_x[0],  y + cross_y[0],  cross_rotn[0], 0.18, False))
                OBJECT_LIST.append(("sign_duck_crossing", x + cross_x[-1], y + cross_y[-1], cross_rotn[1], 0.18, False))
                rotation += [90, 270][random.randint(0, 1)]
                OBJECT_LIST.append((object, x + obj_x, y + obj_y, rotation, DIMS[dim_code][0], False))
            return
        elif ("sign" in object):
            if ("N" in curr_tile) or ("S" in curr_tile):
                cross_x = [0, 1]
                cross_y = [obj_y]
                cross_rotn = [90, 270]
            else:
                cross_y = [0, 1]
                cross_x = [obj_x]
                cross_rotn = [0, 180]
            if ((allowed(map, orig_x, orig_y, x + cross_x[0], y + cross_y[0], dim_code)) and
                (allowed(map, orig_x, orig_y, x + cross_x[-1], y + cross_y[-1], dim_code))
            ):
                OBJECT_LIST.append((object, x + cross_x[0],  y + cross_y[0],  cross_rotn[0], 0.18, False))
                OBJECT_LIST.append((object, x + cross_x[-1], y + cross_y[-1], cross_rotn[1], 0.18, False))
            return
        elif (allowed(map, orig_x, orig_y, x + obj_x, y + obj_y, dim_code)):
            OBJECT_LIST.append((object, x + obj_x, y + obj_y, rotation, DIMS[dim_code][0], False))

    elif ("asphalt" in curr_tile) or ("grass" in curr_tile) or ("floor" in curr_tile):
        obj_x = round(random.uniform(0, 1), 2)
        obj_y = round(random.uniform(0, 1), 2)

        # if an object overflows onto 2 driveable tiles on either side, it cannot be placed
        x_too_wide = 0
        y_too_wide = 0

        # if the second if is true, the first if must be doublechecked
        doublecheck = False
        ctr = 0
        while (ctr < 2):
            ctr += 1
            # if x coord of object overflows onto driveable tile (to the right)
            # if overlaps outside of map, we don't care
            if ((obj_x + DIMS[dim_code][1]) > 1) and (orig_x < len(map[0]) - 1):
                # check if neighbour tile is driveable
                if (not (("grass"   in map[orig_y][orig_x + 1]) or
                         ("floor"   in map[orig_y][orig_x + 1]) or
                         ("asphalt" in map[orig_y][orig_x + 1]))
                ):  # 1.2 and not 1.0 so that white line will be uncovered
                    obj_x -= (obj_x + DIMS[dim_code][1]) - 0.92
                    x_too_wide += 1
                    if (doublecheck):
                        doublecheck = False
                        break
            # if x coord of object is off the tile (to the left)
            if ((obj_x - DIMS[dim_code][1]) < 0) and (orig_x > 0):
                if (not (("grass"   in map[orig_y][orig_x - 1]) or
                         ("floor"   in map[orig_y][orig_x - 1]) or
                         ("asphalt" in map[orig_y][orig_x - 1]))
                ):
                    obj_x += DIMS[dim_code][1] - obj_x + 0.08
                    x_too_wide += 1
                    doublecheck = True

        doublecheck = False
        ctr = 0
        while (ctr < 2):
            ctr +=1
            # if y coord of object is off the tile (under)
            if ((obj_y + DIMS[dim_code][1]) > 1) and (orig_y < len(map) - 1):
                if (not (("grass"   in map[orig_y + 1][orig_x]) or
                         ("floor"   in map[orig_y + 1][orig_x]) or
                         ("asphalt" in map[orig_y + 1][orig_x]))
                ):
                    obj_y -= (obj_y + DIMS[dim_code][1]) - 0.92
                    y_too_wide += 1
                    if (doublecheck):
                        doublecheck = False
                        break
            # if x coord of object is off the tile (over)
            if ((obj_y - DIMS[dim_code][1]) < 0) and (orig_y > 0):
                if (not (("grass"   in map[orig_y - 1][orig_x]) or
                         ("floor"   in map[orig_y - 1][orig_x]) or
                         ("asphalt" in map[orig_y - 1][orig_x]))
                ):
                    obj_y += DIMS[dim_code][1] - obj_y + 0.08
                    y_too_wide += 1
                    doublecheck = True


        # the object is too wide and overlaps onto driveable tiles;
        # cannot be placed
        if (x_too_wide > 1) or (y_too_wide > 1):
            return

        if (object == "house") or (object == "building"):
            rotation = random.randint(1, 4) * 90
        else:
            rotation = round(random.uniform(0, 360), 2)
        if (allowed(map, orig_x, orig_y, x + obj_x, y + obj_y, dim_code)):
            OBJECT_LIST.append((object, x + obj_x, y + obj_y, rotation, DIMS[dim_code][0], False))

    else:
        raise ValueError("unrecognized object string")

    return


# automatically places all signs that are necessary in an intersection,
# according to the duckietown appearance specifications
def signage(sliced_string, x, y):
    global OBJECT_LIST
    if (sliced_string[0] == "4way"):
        signs = (("sign_4_way_intersect",   x - 0.05, y - 0.05, 0),
                 ("sign_t_light_ahead",     x - 0.15, y - 0.05, 270),
                 ("sign_4_way_intersect",   x + 1.05, y - 0.05, 270),
                 ("sign_t_light_ahead",     x + 1.05, y - 0.15, 180),
                 ("sign_4_way_intersect",   x - 0.05, y + 1.05, 90),
                 ("sign_t_light_ahead",     x - 0.05, y + 1.15, 0),
                 ("sign_4_way_intersect",   x + 1.05, y + 1.05, 180),
                 ("sign_t_light_ahead",     x + 1.15, y + 1.05, 90))

    if (sliced_string[0] == "3way"):
        if ("left" == sliced_string[1]):
            conversion = {"N": "S", "E": "W", "S": "N", "W": "E"}
            sliced_string[2] = conversion[sliced_string[2]]

        if (sliced_string[2] == "W"):
            # element format: ("kind", x, y, rotation)
            signs = (("sign_right_T_intersect", x - 0.05, y - 0.05, 0),
                     ("sign_stop",              x + 1.05, y - 0.05, 180),
                     ("sign_stop",              x - 0.05, y + 1.05, 0),
                     ("sign_left_T_intersect",  x + 1.05, y + 1.05, 180),
                     ("sign_left_T_intersect",  x + 1.05, y + 1.05, 180),
                     ("sign_stop",              x + 1.15, y + 1.05, 90))

        elif (sliced_string[2] == "N"):
            signs = (("sign_right_T_intersect", x + 1.05, y - 0.05, 270),
                     ("sign_stop",              x + 1.05, y + 1.05, 90),
                     ("sign_left_T_intersect",  x - 0.05, y + 1.05, 90),
                     ("sign_stop",              x - 0.05, y + 1.15, 0),
                     ("sign_stop",              x - 0.05, y - 0.05, 270),
                     ("sign_T_intersect",       x - 0.05, y - 0.15, 0))

        elif (sliced_string[2] == "E"):
            signs = (("sign_right_T_intersect", x + 1.05, y + 1.05, 180),
                     ("sign_stop",              x - 0.05, y + 1.05, 0),
                     ("sign_stop",              x + 1.05, y - 0.05, 180),
                     ("sign_T_intersect",       x + 1.15, y - 0.05, 270),
                     ("sign_left_T_intersect",  x - 0.05, y - 0.05, 0),
                     ("sign_stop",              x - 0.15, y - 0.05, 270))

        elif (sliced_string[2] == "S"):
            signs = (("sign_stop",              x - 0.05, y - 0.05, 270),
                     ("sign_right_T_intersect", x - 0.05, y + 1.05, 90),
                     ("sign_left_T_intersect",  x + 1.05, y - 0.05, 270),
                     ("sign_stop",              x + 1.05, y - 0.15, 180),
                     ("sign_stop",              x + 1.05, y + 1.05, 90),
                     ("sign_T_intersect",       x + 1.05, y + 1.15, 180))

    try:
        for i in range(0, len(signs)):
            OBJECT_LIST.append((signs[i][0], signs[i][1], signs[i][2], signs[i][3], DIMS["sign"][0], False))

            top_left_x =     signs[i][1] - DIMS["sign"][1]
            top_left_y =     signs[i][2] - DIMS["sign"][1]
            bottom_right_x = signs[i][1] + DIMS["sign"][1]
            bottom_right_y = signs[i][2] + DIMS["sign"][1]
            FILLED_TABLE.append((signs[i][0], top_left_x, top_left_y, bottom_right_x, bottom_right_y, x, y))
    except:
        raise ValueError("sliced string format unrecognized (signs variable therefore undefined)")


def print_objects():
    sys.stdout.write("objects:\n\n")
    for i in range(0, len(OBJECT_LIST)):
        sys.stdout.write("- kind: " + OBJECT_LIST[i][0] + "\n")
        sys.stdout.write("  pos: [" + str(OBJECT_LIST[i][1]) + ", " + str(OBJECT_LIST[i][2]) + "]\n")
        sys.stdout.write("  rotate: " + str(OBJECT_LIST[i][3] % 360) + "\n")
        sys.stdout.write("  height: " + str(OBJECT_LIST[i][4]) + "\n\n")
    sys.stdout.flush()

def write_objects():
    f.write("\r\n")
    f.write("objects:\r\n")
    f.write("\r\n")
    for i in range(0, len(OBJECT_LIST)):
        f.write("- kind: " + OBJECT_LIST[i][0] + "\r\n")
        f.write("  pos: [" + str(OBJECT_LIST[i][1]) + ", " + str(OBJECT_LIST[i][2]) + "]\r\n")
        f.write("  rotate: " + str(OBJECT_LIST[i][3] % 360) + "\r\n")
        f.write("  height: " + str(OBJECT_LIST[i][4]) + "\r\n\r\n")

#===========================================================================================
#===========================================================================================



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate random map using width, \
    height, no_intersections (bool) (optional), density string (optional), no_border (bool) (optional)')
    parser.add_argument('width', type=int)
    parser.add_argument('height', type=int)
    parser.add_argument('--no_intersections', '-ni', action="store_true")
    parser.add_argument('--map_density', '-md', help="options: 'any', 'sparse', 'medium', 'dense'. \n \
                         Note: density not taken into account in maps under 8x8 in size")
    parser.add_argument('--no_border', '-nb', action="store_true")
    parser.add_argument('--obj_density', '-od', help="options: 'empty', 'any', 'sparse', 'medium', 'dense'.")
    parser.add_argument("--road_objects", '-ro', action="store_true")

    args = parser.parse_args()

    if (args.height < 3):
        print("Height too small, please enter a height of 3 or greater.")
        sys.exit()
    if (args.width < 3):
        print("Width too small, please enter a width of 3 or greater.")
        sys.exit()

    if (args.no_intersections):
        has_intersections = False
    else:
        has_intersections = True

    if (args.map_density == "any" or
        args.map_density == "sparse" or
        args.map_density == "medium" or
        args.map_density == "dense"):
        map_density = args.map_density
    else:
        map_density = "any"

    if (args.no_border):
        has_border = False
    else:
        has_border = True

    if (args.obj_density == "empty" or
        args.obj_density == "any" or
        args.obj_density == "sparse" or
        args.obj_density == "medium" or
        args.obj_density == "dense"):
        obj_density = args.map_density
    else:
        obj_density = "empty"

    if (args.road_objects):
        clear_road = False
    else:
        clear_road = True

    main(args.height, args.width, has_intersections, map_density, has_border, obj_density, clear_road)