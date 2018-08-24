import sys
import random
import argparse
import re
import math
import numpy as np

#"""
a = random.randint(0,10000)
print(a)
random.seed(a)
"""
random.seed(1664)
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
TILE_TYPES = (
        "asphalt",
        "grass",
        "floor",
        "straight/N",
        "straight/E",
        "straight/S",
        "straight/W",
        "curve_right/N",
        "curve_right/E",
        "curve_right/S",
        "curve_right/W",
        "curve_left/N",
        "curve_left/E",
        "curve_left/S",
        "curve_left/W",
        "3way_right/N",
        "3way_right/E",
        "3way_right/S",
        "3way_right/W",
        "3way_left/N",
        "3way_left/E",
        "3way_left/S",
        "3way_left/W",
        "4way"
)

# the file onto which we write the output
f = open("output.yaml", "w+")

# generates grid, writes it to file,
# generates objects, writes them to file
def main(map_name, height, width, has_intersections, map_density, has_border, side_objects,
         road_objects, hard_mode, sign_output, matrix_output):
    f.write("tiles:\r\n")
    # if a map file is specified its contents are copied into output.yaml
    if (map_name is not None):
        try:
            input = open(map_name, 'r')
        except:
            raise Exception("The input map file was unable to be opened")
        input.seek(0)
        lines = input.readlines()
        tile_grid = parse_grid(lines)
        height = len(tile_grid)
        width  = len(tile_grid[0])
        input.close()
        # if the file format is not correct, we exit the program
        if(not check_file_format(lines, tile_grid)):
            raise Exception("The input map file does not adhere to the duckietown map format")

    # if there is no file specified, then a width and height MUST be entered for generation
    elif (height == None) or (width == None):
        print("Please specify a valid height and width.")
        sys.exit()

    # otherwise a map is generated
    else:
        tile_grid = gen_tile_grid(height, width, has_intersections, map_density)
        tile_grid = define_inner_empties(height, width, tile_grid)
        if (has_border):
            tile_grid = add_border(tile_grid, height, width)
            height = len(tile_grid)
            width = len(tile_grid[0])

    write_map(tile_grid)
    populate(tile_grid, len(tile_grid), len(tile_grid[0]), side_objects, road_objects, hard_mode)
    if (len(OBJECT_LIST)>0):
        write_objects()
    f.close()

    if (sign_output):
        write_signs()
    if (matrix_output):
        gen_node_graph(tile_grid, height, width)
        write_adj_matrix(height, width)


#===========================================================================================
#============================ GET MAP AND WRITE TO FILE ====================================


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
        node_map = create_map(height, width, has_intersections, density)
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

# parses the text lines from an input file into a 2D array representing the tiles
def parse_grid(lines):
    local_lines = list(lines)
    # remove whitespace
    while ("\n" in local_lines):
        local_lines.remove("\n")
    # pop "tiles:\n"
    local_lines.pop(0)
    tile_grid = []
    for i in range(0, len(local_lines)):
        sliced_string = re.split("[^A-Za-z0-9/_]+", local_lines[i])
        sliced_string.pop(0)
        sliced_string.pop(-1)
        tile_grid.append(sliced_string)

    # remove trailing whitespace
    while (tile_grid[-1] == []):
        tile_grid.pop()

    return tile_grid

# checks that a file passed as an argument is in the right format
def check_file_format(lines, tile_grid):

    tmp_width  = len(tile_grid[0])
    tmp_height = len(tile_grid)

    #remove whitespace
    while("\n" in lines):
        lines.remove("\n")

    if len(lines) != (tmp_height + 1):
        return False

    if (lines[0].strip() != "tiles:"):
        return False

    for i in range (1, len(lines)):
        if (
                (lines[i][:3] != "- [") or (lines[i].strip()[-1:] != "]") or
                (len(tile_grid[i-1]) != tmp_width)
        ):
            return False
    for j in range(0, len(tile_grid)):
        for k in range(0, len(tile_grid[0])):
            if (tile_grid[j][k] not in TILE_TYPES):
                return False

    return True


#======================================== END ==============================================
#===========================================================================================
#=============================== GENERATE ROAD NETWORK =====================================


#========================== GLOBAL VARS / SETUP ===============================
TILE_NEIGHBOURS = {
        "asphalt": (),
        "grass": (),
        "floor": (),
        "straight/N": ("N", "S"),
        "straight/E": ("E", "W"),
        "straight/S": ("N", "S"),
        "straight/W": ("E", "W"),
        "curve_right/N": ("E", "S"),
        "curve_right/E": ("S", "W"),
        "curve_right/S": ("W", "N"),
        "curve_right/W": ("N", "E"),
        "curve_left/N": ("S", "W"),
        "curve_left/E": ("W", "N"),
        "curve_left/S": ("N", "E"),
        "curve_left/W": ("E", "S"),
        "3way_right/N": ("N", "E", "S"),
        "3way_right/E": ("E", "S", "W"),
        "3way_right/S": ("S", "W", "N"),
        "3way_right/W": ("W", "N", "E"),
        "3way_left/N": ("S", "W", "N"),
        "3way_left/E": ("W", "N", "E"),
        "3way_left/S": ("N", "E", "S"),
        "3way_left/W": ("E", "S", "W"),
        "4way": ("N", "E", "S", "W")
}
MAP = []
POSSIBLE_STEPS = []

# elements are of the form (x, y)
ONES = []

# elements are of the form: ( (x, y), "<step_string>", rel_dirs, [steps_left] )
STACK = []

HAS_INTERSECTIONS = True

# closed courses: <---------10---------13---------17--------->
#                  too empty   sparse      medium     dense

#         <----------14%----------18%----------23%---------->
# regular: too empty     sparse       medium       dense
# for now we only use density for regular maps
DENSITY_OPTIONS = {
    #        min%   max%
    "any":    (14, 100),
    "sparse": (14, 18),
    "medium": (18, 23),
    "dense":  (23, 100)
}

#============================= CREATE / MISC ==================================
def create_map(height, width, has_intersections, density):
    global MAP
    global POSSIBLE_STEPS
    global ONES
    global STACK
    global HAS_INTERSECTIONS

    HAS_INTERSECTIONS = has_intersections

    # bounds for map density
    lo_bound = DENSITY_OPTIONS[density][0]
    up_bound = DENSITY_OPTIONS[density][1]

    if (height < 3 or width < 3):
        raise ValueError("ERROR: the map's dimensions are too small. Must be at least 3x3.")

    # density cannot vary sufficiently below dimensions of 7x7;
    # any density is accepted
    if (height < 7 or width < 7) and (density != "any"):
        print("density parameter was changed to 'any'; map dimensions too small ")
        density = "any"

    if (has_intersections):
        POSSIBLE_STEPS = ["straight", "L-curve", "R-curve", "3way", "4way"]
    else:
        POSSIBLE_STEPS = ["straight", "L-curve", "R-curve"]


    for h in range(0, height):
        MAP.append([None]*width)

    for y in range(0, height):
        for x in range(0, width):
            MAP[y][x] = Node(x, y)

    for j in range(0, height):
        for i in range(0, width):
            MAP[j][i].set_neighbours()

    seed_map(height, width)



    # Here, we try and generate a map. If the map is too sparse or dense,
    # or another error occurs during generation, a ValueError is raised,
    # and a new map is generated (recursively).
    try:
        grow()
        ascii_map()
        # max_edges equation explanation:
        #            corners          edges                    interior
        max_edges = ( 2.0*(4) + 3.0*(2*(height+width) - 4) + 4.0*((height-1)*(width-1)) )/2.0
        print("total possible connections: {}".format(max_edges))
        t_r_l = total_road_length()
        print("This map's total road length: {}".format(t_r_l))
        map_density = (float(t_r_l) / float(max_edges)) * 100
        print("Percentage filled: {0:.2f}%".format(map_density))

        # if too sparse for a map with intersections, we generate a new map;
        # a map without intersections will always be more sparse
        if HAS_INTERSECTIONS and ((map_density < lo_bound) or (map_density > up_bound)):
            raise ValueError("Map too sparse or dense")

        coverage = check_coverage(height, width)
        if (not coverage):
            raise ValueError("Insufficient map coverage")

    except ValueError as err:
        print(err.args)
        MAP = []
        POSSIBLE_STEPS = []
        STACK = []
        ONES = []
        MAP = create_map(height, width, has_intersections, density)

    return MAP

def seed_map(height, width):
    global MAP

    poss_seeds = list(POSSIBLE_STEPS)
    # maps smaller than 7 width or height not seeded with intersections;
    # intersections take up too much space
    if (height <= 7) or (width <= 7):
        if ("3way" in poss_seeds):
            poss_seeds.remove("3way")
        if ("4way" in poss_seeds):
            poss_seeds.remove("4way")
    rand_seed = poss_seeds[random.randint(0, len(poss_seeds) - 1)]



    if (rand_seed == "straight"):

        rand_x = random.randint(0, width-1)
        rand_y = random.randint(0, height-1)
        print("random seed coordinates: ({}, {})".format(rand_x, rand_y))

        positions = ["horizontal", "vertical"]
        choice = positions[random.randint(0, len(positions)-1)]
        if (rand_x==0) and (choice == "horizontal"):
            rand_x += 1
        elif (rand_x==width-1) and (choice == "horizontal"):
            rand_x -= 1

        if (rand_y==0) and (choice == "vertical"):
            rand_y += 1
        elif (rand_y==height-1) and (choice == "vertical"):
            rand_y -= 1

        if (choice == "vertical"):
            MAP[rand_y][rand_x].connect("S")
            MAP[rand_y][rand_x].connect("N")
        else:
            MAP[rand_y][rand_x].connect("E")
            MAP[rand_y][rand_x].connect("W")

    elif (rand_seed == "L-curve") or (rand_seed == "R-curve"):

        # a map of height or size 3 is necessarily a ring around its edge
        if (height==3) or (width==3):
            MAP[0][0].connect("S")
            MAP[0][0].connect("E")
            return

        rand_x = random.randint(0, width - 1)
        rand_y = random.randint(0, height - 1)
        print("({}, {})".format(rand_x, rand_y))

        # "N" curve is defined as: |_ ; turned 90 degrees clockwise subsequently
        positions = ["N", "E", "S", "W"]
        if (rand_x <= 1):
            positions.remove("S")
            positions.remove("W")
        if (rand_x >= width-2):
            positions.remove("N")
            positions.remove("E")
        # now, positions may have already been removed, so we test first
        if (rand_y <= 1):
            if ("N" in positions):
                positions.remove("N")
            if ("W" in positions):
                positions.remove("W")
        if (rand_y >= height-2):
            if ("S" in positions):
                positions.remove("S")
            if ("E" in positions):
                positions.remove("E")

        choice = positions[random.randint(0, len(positions) - 1)]
        print(choice)

        if (choice == "N"):
            MAP[rand_y][rand_x].connect("N")
            MAP[rand_y][rand_x].connect("E")
        elif (choice == "E"):
            MAP[rand_y][rand_x].connect("E")
            MAP[rand_y][rand_x].connect("S")
        elif (choice == "S"):
            MAP[rand_y][rand_x].connect("S")
            MAP[rand_y][rand_x].connect("W")
        elif (choice == "W"):
            MAP[rand_y][rand_x].connect("W")
            MAP[rand_y][rand_x].connect("N")



    elif (rand_seed == "3way") and (height >= 7) and (width >= 7):
        rand_x = random.randint(0, width - 1)
        rand_y = random.randint(0, height - 1)

        # "N" curve is defined as: _|_ ; turned 90 degrees clockwise subsequently
        positions = ["N", "E", "S", "W"]
        choice = positions[random.randint(0, len(positions) - 1)]

        if (rand_x<=1) and (choice != "E"):
            rand_x += 2 - rand_x
        elif (rand_x>=width-2) and (choice != "W"):
            rand_x -= 2 - ((width-1) - rand_x)

        if (rand_y<=1) and (choice != "S"):
            rand_y += 2 - rand_y
        elif (rand_y>=height-2) and (choice != "N"):
            rand_y -= 2 - ((height-1) - rand_y)

        if (choice == "N"):
            MAP[rand_y][rand_x].connect("N")
            MAP[rand_y][rand_x].connect("E")
            MAP[rand_y][rand_x].connect("W")
            MAP[rand_y][rand_x].neighbours["N"].connect("N")
            MAP[rand_y][rand_x].neighbours["E"].connect("E")
            MAP[rand_y][rand_x].neighbours["W"].connect("W")
        elif (choice == "E"):
            MAP[rand_y][rand_x].connect("E")
            MAP[rand_y][rand_x].connect("S")
            MAP[rand_y][rand_x].connect("N")
            MAP[rand_y][rand_x].neighbours["E"].connect("E")
            MAP[rand_y][rand_x].neighbours["S"].connect("S")
            MAP[rand_y][rand_x].neighbours["N"].connect("N")
        elif (choice == "S"):
            MAP[rand_y][rand_x].connect("S")
            MAP[rand_y][rand_x].connect("W")
            MAP[rand_y][rand_x].connect("E")
            MAP[rand_y][rand_x].neighbours["S"].connect("S")
            MAP[rand_y][rand_x].neighbours["W"].connect("W")
            MAP[rand_y][rand_x].neighbours["E"].connect("E")
        elif (choice == "W"):
            MAP[rand_y][rand_x].connect("W")
            MAP[rand_y][rand_x].connect("N")
            MAP[rand_y][rand_x].connect("S")
            MAP[rand_y][rand_x].neighbours["W"].connect("W")
            MAP[rand_y][rand_x].neighbours["N"].connect("N")
            MAP[rand_y][rand_x].neighbours["S"].connect("S")


    elif (rand_seed == "4way"):
        rand_x = random.randint(0, width - 1)
        rand_y = random.randint(0, height - 1)

        if (rand_x <= 1):
            rand_x += 2 - rand_x
        elif (rand_x >= width - 2):
            rand_x -= 2 - ((width-1) - rand_x)

        if (rand_y <= 2):
            rand_y += 2 - rand_y
        elif (rand_y >= height - 2):
            rand_y -= 2 - ((height-1) - rand_y)

        MAP[rand_y][rand_x].connect("N")
        MAP[rand_y][rand_x].connect("E")
        MAP[rand_y][rand_x].connect("S")
        MAP[rand_y][rand_x].connect("W")
        MAP[rand_y][rand_x].neighbours["N"].connect("N")
        MAP[rand_y][rand_x].neighbours["E"].connect("E")
        MAP[rand_y][rand_x].neighbours["S"].connect("S")
        MAP[rand_y][rand_x].neighbours["W"].connect("W")


    else:
        raise ValueError("ERROR: unrecognized rand_seed string: {}".format(rand_seed))

    ascii_map()
    return


# finds all nodes of degree x
def scan_for_degx(x):
    global MAP
    local_Xs = []
    for j in range(0, len(MAP)):
        for i in range(0, len(MAP[0])):
            if (MAP[j][i].deg() == x):
                local_Xs.append( (i, j) )
    return local_Xs

def find_leading_connection(node):
    if(node.deg() == 1):
        for key, value in node.connected.items():
            if (value == 1):
                return key
    else:
        raise ValueError("ERROR: trying to find leading connection on deg 2+ node")


def total_road_length():
    global MAP
    # overall sum of the degrees of all nodes
    total = 0
    for j in range(0, len(MAP)):
        for i in range(0, len(MAP[0])):
            total += MAP[j][i].deg()
    # each connection exists in 2 nodes, so we halve the total
    return total / 2

# check if generated map makes good use of dimensions
# (we don't want to have all the road in one area)
# we do this by checking that each quadrant of the map has
# at least some road in it
def check_coverage(height, width):
    if (HAS_INTERSECTIONS):
        min = 2
    else:
        min = 3
    quadrant_height = int( math.ceil(height / 4.0) )
    quadrant_width  = int( math.ceil(width  / 4.0) )

    # the start and end indices for the 4 quadrants
    indices = [(0,                      quadrant_height, 0,                      quadrant_width),
               (0,                      quadrant_height, width-quadrant_width, width),
               (height-quadrant_height, height,          0,                      quadrant_width),
               (height-quadrant_height, height,          width-quadrant_width, width)]
    # number of quadrants of the map with road in it
    num_covered = 0
    for k in range(0,4):
        # covered is True if the current quadrant has at least one road piece in it
        covered = False
        for j in range(indices[k][0], indices[k][1]):
            for i in range(indices[k][2], indices[k][3]):
                if (MAP[j][i].deg() != 0):
                    covered = True
                    break
        if (covered):
            num_covered += 1

    if (num_covered >= min):
        return True
    else:
        return False



# returns set of relative directions on a degree 1 node
# according to its only connection
def find_rel_dirs(leading_connection):
    if (leading_connection == "S"):
        return {"f": "N",  # relative forward "f" is north "N"
                "r": "E",  # relative right "r" is east "E"
                "b": "S",  # relative backwards "b" is south "S"
                "l": "W"}  # relative left "l" is west "W"
    elif (leading_connection == "W"):
        return {"f": "E",
                "r": "S",
                "b": "W",
                "l": "N"}
    elif (leading_connection == "N"):
        return {"f": "S",
                "r": "W",
                "b": "N",
                "l": "E"}
    elif (leading_connection == "E"):
        return {"f": "W",
                "r": "N",
                "b": "E",
                "l": "S"}
    else:
        raise ValueError("ERROR: unrecognized direction string")


def ascii_map():
    global MAP
    for j in range(0, len(MAP)):
        down_edges = []
        right_edges = []
        # fill up arrays
        for i in range(0, len(MAP[0])):
            if (MAP[j][i].connected["E"] == 1):
                right_edges.append(str(MAP[j][i].deg()) + "-")
            else:
                right_edges.append(str(MAP[j][i].deg()) + " ")

            if (MAP[j][i].connected["S"] == 1):
                down_edges.append("| ")
            else:
                down_edges.append("  ")

        # print right edges
        for k in range(0, len(right_edges)):
            sys.stdout.write(right_edges[k])
        sys.stdout.write("\n")

        # print down edges
        for m in range(0, len(down_edges)):
            sys.stdout.write(down_edges[m])
        sys.stdout.write("\n")

    sys.stdout.write("() \n")
    sys.stdout.flush()

def print_stack():
    sys.stdout.write("STACK: [")
    for i in range(0,len(STACK)):
        sys.stdout.write("[(" + str(STACK[i][0].x) + ", " + str(STACK[i][0].y) + "); " + STACK[i][1] + "]")
    sys.stdout.write("] \n")
    sys.stdout.flush()

# Makes a node graph to be used to output an adjacency matrix (--matrix-output).
# Note: this function overwrites MAP, this avoids problems in case a border
# was added to map after generation.
def gen_node_graph(tile_grid, height, width):
    global MAP
    MAP = [[None for x in range(width)] for y in range(height)]

    #initialize the nodes
    for y in range(0, height):
        for x in range(0, width):
            MAP[y][x] = Node(x, y)

    for j in range(0, height):
        for i in range(0, width):
            MAP[j][i].set_neighbours()

    for b in range(0, height):
        for a in range(0, width):
            try:
                neighbs = TILE_NEIGHBOURS[tile_grid[b][a]]
            except:
                raise ValueError("string '{}' in tile_grid not recognized".format(tile_grid[b][a]))

            for c in range(0, len(neighbs)):
                if not (MAP[b][a].connected[neighbs[c]]):
                    MAP[b][a].connect(neighbs[c])


def write_adj_matrix(height, width):
    out = np.zeros(shape=(height * width, height * width), dtype='uint8')
    for j in range(0, height):
        for i in range(0, height):
            curr_node = MAP[j][i]
            #look at east and south neighbours - will cover every connection overall
            if (curr_node.connected["E"]):
                # Adj: y-coord is the neighbour, x-coord is the current
                out[j * width + (i + 1)][j * width + i] = 1
            if (curr_node.connected["S"]):
                out[(j + 1) * width + i][j * width + i] = 1
    dims = (height, width)
    np.savez("adj_matrix.npz", out=out, dims=dims)



#================================= GROW =======================================
def grow():

    backtracked = False
    ctr = 0
    while (len(ONES) > 0) and (ctr < 10000):
        ctr += 1
        #ascii_map()
        # If the last step created a deg 3 node when the map
        # is to have NO INTERSECTIONS, then we backtrack
        if (not HAS_INTERSECTIONS) and (len(scan_for_degx(3)) > 0):
            # if map is well covered, trimming is likely to produce a good map
            if (check_coverage(len(MAP), len(MAP[0]))):
                trim()
                continue
            # otherwise, backtrack to find better solution
            else:
                backtrack()
                backtracked = True
                continue

        if (backtracked):
            if(len(STACK)==0):
                raise ValueError("We backtracked all the way to the seed. Either null set or backtracking error.")
            else:
                top_stack = STACK.pop(-1)
                next = top_stack[0]
                rel_dirs = top_stack[2]
                options_left = top_stack[3]
                backtracked = False
                if len(options_left) == 0:
                    backtrack()
                    backtracked = True
                    continue
        else:
            next = MAP[ONES[-1][1]][ONES[-1][0]]
            rel_dirs = find_rel_dirs(find_leading_connection(next))
            options_left = list(POSSIBLE_STEPS)

        while (len(options_left) > 0):
            rand_step = options_left[random.randint(0, len(options_left)-1)]
            if (is_safe(next,rand_step, rel_dirs)):
                options_left.remove(rand_step)
                STACK.append([next, rand_step, rel_dirs, options_left])
                prev_cxns = step(next, rand_step, rel_dirs)
                STACK[-1].append(prev_cxns)
                break
            else:
                options_left.remove(rand_step)
                if (len(options_left) == 0):
                    if (STACK[-1][1] == ""):
                        raise ValueError("ERROR: Trying to backtrack from NO STEP")
                    else:
                        backtrack()
                        backtracked = True
            sys.stdout.flush()

    # if generation has taken more than 2 seconds, we "trim" the network;
    # remove elements of ONES until map is valid
    if (len(ONES) > 0):
        trim()




#============================ STEP ALGORITHMS =================================
# backtracks: pops last move from STACK and undoes last step
def backtrack():
    top_stack = STACK[-1]
    node = top_stack[0]
    last_step = top_stack[1]
    rel_dirs = top_stack[2]
    prev_cxns = top_stack[4]

    if (last_step == "straight"):
        node.disconnect(rel_dirs["f"])

    elif (last_step == "L-curve"):
        node.disconnect(rel_dirs["l"])

    elif (last_step == "R-curve"):
        node.disconnect(rel_dirs["r"])

    elif (last_step == "3way"):
        node.neighbours[rel_dirs["l"]].disconnect(rel_dirs["l"])
        node.neighbours[rel_dirs["r"]].disconnect(rel_dirs["r"])
        node.disconnect(rel_dirs["l"])
        node.disconnect(rel_dirs["r"])

    elif (last_step == "4way"):
        node.neighbours[rel_dirs["l"]].disconnect(rel_dirs["l"])
        node.neighbours[rel_dirs["r"]].disconnect(rel_dirs["r"])
        node.neighbours[rel_dirs["f"]].disconnect(rel_dirs["f"])
        node.disconnect(rel_dirs["l"])
        node.disconnect(rel_dirs["r"])
        node.disconnect(rel_dirs["f"])

    else:
        raise ValueError("ERROR: unrecognized last_step string: {}".format(last_step))

    # re-establish connections that existed before the step from which we're backtracking;
    # there may have been overlap, and we don't want to remove road from a different step
    for i in range(0, len(prev_cxns)):
        node.neighbours[rel_dirs[prev_cxns[i][0]]].connect(rel_dirs[prev_cxns[i][1]])




# performs the specified next step
def step(node, next_step, rel_dirs):
    # keep track of previously established connections; for use in backtracking
    prev_cxns = []
    if (next_step == "straight"):
        node.connect(rel_dirs["f"])

    elif (next_step == "L-curve"):
        node.connect(rel_dirs["l"])

    elif (next_step == "R-curve"):
        node.connect(rel_dirs["r"])

    elif (next_step == "3way"):
        # direct left and right neighbours have been connected in check_3way()
        if node.neighbours[rel_dirs["l"]].connected[rel_dirs["l"]]:
            prev_cxns.append(["l","l"])
        else:
            node.neighbours[rel_dirs["l"]].connect(rel_dirs["l"])

        if node.neighbours[rel_dirs["r"]].connected[rel_dirs["r"]]:
            prev_cxns.append(["r","r"])
        else:
            node.neighbours[rel_dirs["r"]].connect(rel_dirs["r"])

    elif (next_step == "4way"):
        # direct left, right, and forward neighbours have been connected in check_4way()
        if node.neighbours[rel_dirs["l"]].connected[rel_dirs["l"]]:
            prev_cxns.append(["l", "l"])
        else:
            node.neighbours[rel_dirs["l"]].connect(rel_dirs["l"])

        if node.neighbours[rel_dirs["r"]].connected[rel_dirs["r"]]:
            prev_cxns.append(["r", "r"])
        else:
            node.neighbours[rel_dirs["r"]].connect(rel_dirs["r"])

        if node.neighbours[rel_dirs["f"]].connected[rel_dirs["f"]]:
            prev_cxns.append(["f", "f"])
        else:
            node.neighbours[rel_dirs["f"]].connect(rel_dirs["f"])

    else:
        raise ValueError("ERROR: unrecognized next_step string: {}".format(next_step))

    return prev_cxns



def trim():
    global MAP
    print("We're trimming.")
    while (len(ONES)):
        old_len = len(ONES)
        new_len = len(ONES)
        while (old_len == new_len):
            curr_node = MAP[ONES[-1][1]][ONES[-1][0]]
            rel_dirs = find_rel_dirs(find_leading_connection(curr_node))
            curr_node.disconnect(rel_dirs["b"])
            new_len = len(ONES)

        if (new_len>old_len):
            raise ValueError("Somehow trim made us gain ONES")




#======================== SAFETY & CHECK ALGORITHMS ===========================
# LOGIC BEHIND "CHECK" FUNCTIONS IS EXPLAINED IN check_explanations FOLDER

def is_safe(node, next_step, rel_dirs):
    if (next_step == "straight"):
        return check_straight(node, rel_dirs)

    elif (next_step == "L-curve"):
        return check_L_curve(node, rel_dirs)

    elif (next_step == "R-curve"):
        return check_R_curve(node, rel_dirs)

    elif (next_step == "3way"):
        return check_3way(node, rel_dirs)

    elif (next_step == "4way"):
        return check_4way(node, rel_dirs)

    else:
        raise ValueError("ERROR: unrecognized next_step string: {}".format(next_step))


def check_straight(node, rel_dirs): #1 <- refers to case number in check_straight.png
    if ((node.neighbours[rel_dirs["r"]] is None or
         node.neighbours[rel_dirs["r"]].deg() == 0)
       and
        (node.neighbours[rel_dirs["l"]] is None or
         node.neighbours[rel_dirs["l"]].deg() == 0)
    ): #1
        if(node.neighbours[rel_dirs["f"]] is None): # 1.1
            return False

        # if on the top edge
        elif (node.neighbours[rel_dirs["f"]].neighbours[rel_dirs["f"]] is None): # 1.2
            return True

        # if on the left edge (with space in front)
        elif((node.neighbours[rel_dirs["l"]] is None) and   # 1.3
              node.neighbours[rel_dirs["r"]].deg() == 0):
            if (node.neighbours[rel_dirs["f"]].connected[rel_dirs["f"]]):   #1.3.1
                return True
            else:   # 1.3.2
                # we now allocate variables for code legibility
                c = node.neighbours[rel_dirs["f"]].neighbours[rel_dirs["f"]].neighbours[rel_dirs["r"]]
                b = node.neighbours[rel_dirs["f"]].neighbours[rel_dirs["f"]]
                e = node.neighbours[rel_dirs["f"]].neighbours[rel_dirs["r"]]
                if (c.deg() == 0): #1.3.2.1
                    return True
                elif (c.connected[rel_dirs["l"]] and e.deg() > 0): #1.3.2.2
                    return False
                elif (c.connected[rel_dirs["b"]] and b.deg() > 0): #1.3.2.3
                    return False
                else: # 1.3.2.4
                    return True

        # if on the right edge (with space in front)
        elif ((node.neighbours[rel_dirs["r"]] is None) and  # 1.4
              node.neighbours[rel_dirs["l"]].deg() == 0):
            if (node.neighbours[rel_dirs["f"]].connected[rel_dirs["f"]]): # 1.4.1
                return True
            else: # 1.4.2
                # we now allocate variables for code legibility
                a = node.neighbours[rel_dirs["f"]].neighbours[rel_dirs["f"]].neighbours[rel_dirs["l"]]
                b = node.neighbours[rel_dirs["f"]].neighbours[rel_dirs["f"]]
                d = node.neighbours[rel_dirs["f"]].neighbours[rel_dirs["l"]]
                if (a.deg() == 0): # 1.4.2.1
                    return True
                elif (a.connected[rel_dirs["r"]] and d.deg() > 0): # 1.4.2.2
                    return False
                elif (a.connected[rel_dirs["b"]] and b.deg() > 0): # 1.4.2.3
                    return False
                else: #1.4.2.3
                    return True


        # if in open space
        elif((node.neighbours[rel_dirs["l"]].deg() == 0) and  # 1.5
             (node.neighbours[rel_dirs["r"]].deg() == 0)):
            # we now allocate variables for code legibility
            a = node.neighbours[rel_dirs["f"]].neighbours[rel_dirs["f"]].neighbours[rel_dirs["l"]]
            b = node.neighbours[rel_dirs["f"]].neighbours[rel_dirs["f"]]
            c = node.neighbours[rel_dirs["f"]].neighbours[rel_dirs["f"]].neighbours[rel_dirs["r"]]
            d = node.neighbours[rel_dirs["f"]].neighbours[rel_dirs["l"]]
            e = node.neighbours[rel_dirs["f"]].neighbours[rel_dirs["r"]]
            if (node.neighbours[rel_dirs["f"]].connected[rel_dirs["f"]]): # 1.5.1

                if (                                                      # P1 (manual bug fix)
                        (node.neighbours[rel_dirs["f"]].connected[rel_dirs["r"]] or
                         node.neighbours[rel_dirs["f"]].connected[rel_dirs["l"]])
                        and
                        (b.connected[rel_dirs["l"]] or
                         b.connected[rel_dirs["r"]])
                ):
                    return False
                else:
                    return True
            else: #1.5.2
                if (a.deg() == 0 and c.deg() == 0): # 1.5.2.1
                    return True
                elif (a.deg() > 0 and c.deg() == 0): # 1.5.2.2
                    if (a.connected[rel_dirs["r"]] and (d.deg()>0 or e.deg()>0)): # 1.5.2.2.1
                        return False
                    elif (a.connected[rel_dirs["b"]] and (b.deg()>0 or e.deg()>0)): # 1.5.2.2.2
                        return False
                    else: # 1.5.2.2.3
                        return True
                elif (a.deg() == 0 and c.deg() > 0):  # 1.5.2.3
                    if (c.connected[rel_dirs["l"]] and (e.deg()>0 or d.deg()>0)):  # 1.5.2.3.1
                        return False
                    elif (c.connected[rel_dirs["b"]] and (b.deg()>0 or d.deg()>0)): # 1.5.2.3.2
                        return False
                    else:  # 1.5.2.3.3
                        return True
                elif (a.deg() > 0 and c.deg() > 0): # 1.5.2.4
                    if (a.connected[rel_dirs["b"]]):  # 1.5.2.4.1
                        if (c.connected[rel_dirs["l"]] or c.connected[rel_dirs["b"]]):  # 1.5.2.4.1.1
                            return False
                        else: # 1.5.2.4.1.2
                            return True
                    elif (c.connected[rel_dirs["b"]]):  # 1.5.2.4.2
                        if (a.connected[rel_dirs["r"]] or a.connected[rel_dirs["b"]]): # 1.5.2.4.2.1
                            return False
                        else:  # 1.5.2.4.2.1
                            return True
                    else: # 1.5.2.4.3
                        return True
                else:
                    raise ValueError('ERROR: untreated topology in straight')
        else:
            raise ValueError('ERROR: untreated topology in straight')
    else: #2
        return False


def check_L_curve(node, rel_dirs):
    if ((node.neighbours[rel_dirs["f"]] is None or
         node.neighbours[rel_dirs["f"]].deg() == 0)
         and
        (node.neighbours[rel_dirs["r"]] is None or
         node.neighbours[rel_dirs["r"]].deg() == 0)
         and
        (node.neighbours[rel_dirs["l"]] is not None)
         and
        (node.neighbours[rel_dirs["l"]].neighbours[rel_dirs["b"]].deg() == 0)
         and
        (node.neighbours[rel_dirs["b"]].deg() < 3)
    ):
        b = node.neighbours[rel_dirs["l"]].neighbours[rel_dirs["l"]]
        e = node.neighbours[rel_dirs["l"]].neighbours[rel_dirs["f"]]
        if ( (b is None) ):
            if (e is None):                 # corner case
                return False
            else:
                return True
        elif(e is None):                    # edge case
            return True
        elif (b.deg()>0 and e.deg()>0):     # general rule
            return False
        else:
            return True
    else:
        return False

def check_R_curve(node, rel_dirs):
    if ((node.neighbours[rel_dirs["f"]] is None or
         node.neighbours[rel_dirs["f"]].deg() == 0)
         and
        (node.neighbours[rel_dirs["l"]] is None or
         node.neighbours[rel_dirs["l"]].deg() == 0)
         and
        (node.neighbours[rel_dirs["r"]] is not None)
         and
        (node.neighbours[rel_dirs["r"]].neighbours[rel_dirs["b"]].deg() == 0)
         and
        (node.neighbours[rel_dirs["b"]].deg() < 3)
    ):
        b = node.neighbours[rel_dirs["r"]].neighbours[rel_dirs["r"]]
        d = node.neighbours[rel_dirs["r"]].neighbours[rel_dirs["f"]]
        if (b is None):
            if (d is None):                 # corner case
                return False
            else:
                return True
        elif (d is None):                   # edge case
            return True
        elif (b.deg()>0 and d.deg()>0):     # general rule
            return False
        else:
            return True
    else:
        return False

# a 3way must lead into all straight tiles
# because of this, we make use of check_straight() on either side
def check_3way(node, rel_dirs):
    if ((node.neighbours[rel_dirs["r"]] is not None)
         and
        (node.neighbours[rel_dirs["l"]] is not None)
         and
        (node.neighbours[rel_dirs["f"]] is None or
         node.neighbours[rel_dirs["f"]].deg() == 0)
         and
        (node.neighbours[rel_dirs["b"]].connected[rel_dirs["b"]])
         and not
        (node.neighbours[rel_dirs["b"]].connected[rel_dirs["l"]] or
         node.neighbours[rel_dirs["b"]].connected[rel_dirs["r"]])
    ):
        node.connect(rel_dirs["l"])
        L_rel_dirs = find_rel_dirs(rel_dirs["r"])
        L_result = check_straight(node.neighbours[rel_dirs["l"]], L_rel_dirs)

        node.connect(rel_dirs["r"])
        R_rel_dirs = find_rel_dirs(rel_dirs["l"])
        R_result = check_straight(node.neighbours[rel_dirs["r"]], R_rel_dirs)

        if (R_result and L_result):
            return True
        else:
            node.disconnect(rel_dirs["l"])
            node.disconnect(rel_dirs["r"])
            return False
    else:
        return False


def check_4way(node, rel_dirs):
    if ((node.neighbours[rel_dirs["r"]] is not None)
         and
        (node.neighbours[rel_dirs["l"]] is not None)
         and
        (node.neighbours[rel_dirs["f"]] is not None)
         and
        (node.neighbours[rel_dirs["b"]].connected[rel_dirs["b"]])
         and not
        (node.neighbours[rel_dirs["b"]].connected[rel_dirs["l"]] or
         node.neighbours[rel_dirs["b"]].connected[rel_dirs["r"]])
    ):
        if (node.neighbours[rel_dirs["f"]].neighbours[rel_dirs["l"]].deg() > 0 or
            node.neighbours[rel_dirs["f"]].neighbours[rel_dirs["r"]].deg() > 0):
            return False
        else:
            node.connect(rel_dirs["l"])
            L_rel_dirs = find_rel_dirs(rel_dirs["r"])
            L_result = check_straight(node.neighbours[rel_dirs["l"]], L_rel_dirs)

            node.connect(rel_dirs["r"])
            R_rel_dirs = find_rel_dirs(rel_dirs["l"])
            R_result = check_straight(node.neighbours[rel_dirs["r"]], R_rel_dirs)

            node.connect(rel_dirs["f"])
            F_result = check_straight(node.neighbours[rel_dirs["f"]], rel_dirs)

            if (R_result and L_result and F_result):
                return True
            else:
                node.disconnect(rel_dirs["l"])
                node.disconnect(rel_dirs["r"])
                node.disconnect(rel_dirs["f"])
                return False
    else:
        return False


class Node():
    global MAP
    def __init__(self, x, y):
        # cartesian coordinates in the map
        self.x = x
        self.y = y

        # the neighbouring Nodes
        self.neighbours = {"N":None, "E":None, "S":None, "W":None}

        # represents if self is connected to neighbours
        self.connected = {"N":0, "E":0, "S":0, "W":0}

    def deg(self):
        return self.connected["N"] + self.connected["E"] + \
               self.connected["S"] + self.connected["W"]

    def connect(self, direction):
        if (self.neighbours[direction] is not None):
            global ONES
            # connect on self's side
            if (self.deg() == 0):
                ONES.append((self.x, self.y))
            elif (self.deg() == 1):
                ONES.remove((self.x, self.y))
            self.connected[direction] = 1

            # connect on the conectee's side
            if (self.neighbours[direction].deg()==0):
                ONES.append((self.neighbours[direction].x, self.neighbours[direction].y))
            elif (self.neighbours[direction].deg()==1):
                ONES.remove((self.neighbours[direction].x, self.neighbours[direction].y))

            if   direction == "N":
                self.neighbours[direction].connected["S"] = 1
            elif direction == "E":
                self.neighbours[direction].connected["W"] = 1
            elif direction == "S":
                self.neighbours[direction].connected["N"] = 1
            elif direction == "W":
                self.neighbours[direction].connected["E"] = 1
        else:
            raise ValueError('ERROR: tried to connect "{}" to non-existant node from ({}, {})'.format(direction, str(self.x), str(self.y)))


    def disconnect(self, direction):
        if (self.neighbours[direction] is not None):
            global ONES
            # disconnect on self's side
            if (self.deg() == 1):
                ONES.remove((self.x, self.y))
            elif (self.deg() == 2):
                ONES.append((self.x, self.y))
            self.connected[direction] = 0


            # disconnect on the disconectee's side
            if (self.neighbours[direction].deg() == 1):
                ONES.remove((self.neighbours[direction].x, self.neighbours[direction].y))
            elif (self.neighbours[direction].deg() == 2):
                ONES.append((self.neighbours[direction].x, self.neighbours[direction].y))

            if   direction == "N":
                self.neighbours[direction].connected["S"] = 0
            elif direction == "E":
                self.neighbours[direction].connected["W"] = 0
            elif direction == "S":
                self.neighbours[direction].connected["N"] = 0
            elif direction == "W":
                self.neighbours[direction].connected["E"] = 0
        else:
            raise ValueError("ERROR: tried to connect to non-existant node")



    # IMPORTANT: Y-axis comes before X-axis due to how 2D arrays are represented
    # ( MAP[y][x] );    ex. MAP[5][0] => cartesian coordinates (0, 5)
    def set_neighbours(self):
        # north neighbour
        # if node is in the top row (y == 0), self.neighbours["N"] remains None
        try:
            if (self.y > 0):
                self.neighbours["N"] = MAP[self.y - 1][self.x]
        except:
            raise ValueError("ERROR: undefined north neighbour")

        # east neighbour
        # if node is in the rightmost column (x == len(MAP[0])-1), self.neighbours["E"] remains None
        try:
            if (self.x < len(MAP[0])-1):
                self.neighbours["E"] = MAP[self.y][self.x + 1]
        except:
            raise ValueError("ERROR: undefined east neighbour")

        # south neighbour
        # if node is in the bottom row (y == len(MAP)), self.neighbours["S"] remains None
        try:
            if (self.y < len(MAP)-1):
                self.neighbours["S"] = MAP[self.y + 1][self.x]
        except:
            raise ValueError("ERROR: undefined south neighbour")

        # west neighbour
        # if node is in the leftmost column (x == 0), self.neighbours["W"] remains None
        try:
            if (self.x > 0):
                self.neighbours["W"] = MAP[self.y][self.x - 1]
        except:
            raise ValueError("ERROR: undefined west neighbour")




#====================================== END ==============================================
#===========================================================================================
#============================= POPULATE MAP WITH OBJECTS ===================================

# list of objects to be written to file
# element format: ( "kind", x, y, rotation, height, optional )
OBJECT_LIST = []

# list of objects to be used for avoiding object overlap
# element format: ("kind", top-left_x, top-left_y, bottom-right_x, bottom-right_y, tile_x, tile_y)
FILLED_TABLE = []

NUM_SIDE_OBJECTS = 0
NUM_ROAD_OBJECTS = 0

HARD_MODE = False

# Dimensions.
# Element format -> "type": (z-height, ~radius)
DIMS = {
    "barrier": (0.08, 0.25),
    "cone": (0.08, 0.04),
    "duckie": (0.04, 0.04),   # (pedestrian)
    "duckiebot": (0.1, 0.1),  # (car)
    "tree": (0.25, 0.1),
    "house": (0.5, 0.6),
    "truck": (0.2, 0.2),
    "bus": (0.18, 0.45),
    "building": (0.6, 0.49),
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

# initialises variables needed for object generation,
# calls place_object(), when appropriate, to do the hard work
# (map is a 2D array of tile strings)
def populate(map, height, width, side_objects, road_objects, hard_mode):
    global NUM_ROAD_OBJECTS
    global NUM_SIDE_OBJECTS
    global TILE_OPTIONS
    global FILLED_TABLE
    global HARD_MODE

    HARD_MODE = hard_mode

    # number of tiles where objects may be placed
    num_side = 0
    num_road = 0
    for d in range(0, height):
        for c in range(0, width):
            if ("grass" in map[d][c]) or ("floor" in map[d][c]) or ("asphalt" in map[d][c]):
                num_side += 1
            elif ("3way" not in map[d][c]) and ("4way" not in map[d][c]):
                # if normal difficulty and one of neighbours is an intersection, continue
                if (
                        (not hard_mode)   and (
                        ((c < width - 1)  and (("3way" in map[d][c + 1]) or ("4way" in map[d][c + 1]))) or
                        ((c > 0)          and (("3way" in map[d][c - 1]) or ("4way" in map[d][c - 1]))) or
                        ((d < height - 1) and (("3way" in map[d + 1][c]) or ("4way" in map[d + 1][c]))) or
                        ((d > 0)          and (("3way" in map[d - 1][c]) or ("4way" in map[d - 1][c])))
                )):
                    continue
                else:
                    num_road += 1
    if (side_objects == "any"):
        side_objects = ["empty", "sparse", "medium", "dense"][random.randint(0, 3)]

    if (side_objects == "empty"):
        NUM_SIDE_OBJECTS = 0
    elif (side_objects == "sparse"):
        NUM_SIDE_OBJECTS = int(round(num_side * 0.1))
    elif (side_objects == "medium"):
        NUM_SIDE_OBJECTS = int(round(num_side * 0.2))
    else:  # dense
        NUM_SIDE_OBJECTS = int(round(num_side * 0.3))


    if (road_objects == "any"):
        road_objects = ["empty", "sparse", "medium", "dense"][random.randint(0, 3)]
    # if empty, then we allow some signs on the sides of driveable tiles
    if (road_objects == "empty"):
        NUM_ROAD_OBJECTS = int(round(num_road * 0.1))
        TILE_OPTIONS["straight"] = ("sign")
        TILE_OPTIONS["curve"] = ("sign")
    elif (road_objects == "sparse"):
        NUM_ROAD_OBJECTS = int(round(num_road * 0.1))
    elif (road_objects == "medium"):
        NUM_ROAD_OBJECTS = int(round(num_road * 0.2))
    else:  # dense
        NUM_ROAD_OBJECTS = int(round(num_road * 0.3))

    # useful for density testing
    #print("\n# side tiles: {}, # side objects: {}".format(num_side, NUM_SIDE_OBJECTS))
    #print("# road tiles: {}, # road objects: {}".format(num_road, NUM_ROAD_OBJECTS))


    # 2D array where each element has a list of objects that may be placed,
    # based on the type of tile at the corresponding coordinates
    poss_table = [[None for x in range(width)] for y in range(height)]
    for j in range(0, height):
        for i in range(0, width):
            sliced_string = re.split("[^A-Za-z0-9]+", map[j][i])

            if (sliced_string[0] == "4way") or (sliced_string[0] == "3way"):
                signage(sliced_string, i, j)
                continue
            poss_table[j][i] = TILE_OPTIONS[sliced_string[0]]

    # If the random coordinates are that of a tile on which objects may be placed,
    # place_object() is called.
    # Object will only actually be placed if there is no collision with existing ones.
    #
    # This "while" populates non-driveable tiles
    num_signs = len(OBJECT_LIST) + 0
    while (len(OBJECT_LIST) < NUM_SIDE_OBJECTS + num_signs):
        x = random.randint(0, width  - 1)
        y = random.randint(0, height - 1)

        if (
                ("3way" not in map[y][x]) and ("4way" not in map[y][x])
                and (("grass" in map[y][x]) or ("floor" in map[y][x]) or ("asphalt" in map[y][x]))
        ):
            # what can be placed on the current type of tile
            sliced_string = re.split("[^A-Za-z0-9]+", map[y][x])
            curr_options = TILE_OPTIONS[sliced_string[0]]
            object = curr_options[random.randint(0, len(curr_options) - 1)]

            # place it
            place_object(map, object, x, y, sliced_string)

    # This "while" populates driveable tiles
    while (len(OBJECT_LIST) < NUM_ROAD_OBJECTS + NUM_SIDE_OBJECTS + num_signs):
        x = random.randint(0, width  - 1)
        y = random.randint(0, height - 1)

        if (
                ("3way" not in map[y][x]) and ("4way" not in map[y][x])
                and (("straight" in map[y][x]) or ("curve" in map[y][x]))
        ):
            # if normal difficulty and one of neighbours is an intersection, continue
            if (
                    (not hard_mode)   and (
                    ((x < width - 1)  and (("3way" in map[y][x + 1]) or ("4way" in map[y][x + 1]))) or
                    ((x > 0)          and (("3way" in map[y][x - 1]) or ("4way" in map[y][x - 1]))) or
                    ((y < height - 1) and (("3way" in map[y + 1][x]) or ("4way" in map[y + 1][x]))) or
                    ((y > 0)          and (("3way" in map[y - 1][x]) or ("4way" in map[y - 1][x])))
            )):
                continue
            else:
                # what can be placed on the current type of tile
                sliced_string = re.split("[^A-Za-z0-9]+", map[y][x])
                curr_options = TILE_OPTIONS[sliced_string[0]]
                # if there is only one option for a given tile type
                if isinstance(curr_options, str):
                    object = curr_options
                else:
                    object = curr_options[random.randint(0, len(curr_options) - 1)]

                # place it
                place_object(map, object, x, y, sliced_string)




def allowed(map, orig_x, orig_y, obj_x, obj_y, object):
    global FILLED_TABLE

    curr_tile = map[orig_y][orig_x]

    # extremities of object
    top_left_x     = obj_x - DIMS[object][1]
    top_left_y     = obj_y - DIMS[object][1]
    bottom_right_x = obj_x + DIMS[object][1]
    bottom_right_y = obj_y + DIMS[object][1]

    # Curves and straights cannot have two non-sign objects;
    # becomes too hard to navigate.
    if ("curve" in curr_tile) or ("straight" in curr_tile):
        # If normal difficulty, a tile with a neighbouring curve
        # that has objects must be empty
        if (not HARD_MODE):
            # check if each object is in a neighbouring curve
            for i in range(0, len(FILLED_TABLE)):
                # if RIGHT neighbour is a curve
                if (
                        (orig_x < len(map[0]) - 1) and
                        ("curve" in map[orig_y][orig_x + 1]) and
                        (FILLED_TABLE[i][5] == orig_x + 1) and
                        (FILLED_TABLE[i][6] == orig_y)
                ):
                    return
                # if LEFT neighbour is a curve
                if (
                        (orig_x > 0) and
                        ("curve" in map[orig_y][orig_x - 1]) and
                        (FILLED_TABLE[i][5] == orig_x - 1) and
                        (FILLED_TABLE[i][6] == orig_y)
                ):
                    return
                # if LOWER neighbour is a curve
                if (
                        (orig_y < len(map) - 1) and
                        ("curve" in map[orig_y + 1][orig_x]) and
                        (FILLED_TABLE[i][5] == orig_x) and
                        (FILLED_TABLE[i][6] == orig_y + 1)
                ):
                    return
                # if UPPER neighbour is a curve
                if (
                        (orig_y > 0) and
                        ("curve" in map[orig_y - 1][orig_x]) and
                        (FILLED_TABLE[i][5] == orig_x) and
                        (FILLED_TABLE[i][6] == orig_y - 1)
                ):
                    return


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
            #conversion = {"N": "S", "E": "W", "S": "N", "W": "E"}
            conversion = {"N": "E", "E": "S", "S": "W", "W": "N"}
            sliced_string[2] = conversion[sliced_string[2]]
        #if ("right" == sliced_string[1]):
        #    conversion = {"N": "E", "E": "S", "S": "W", "W": "N"}
        #    sliced_string[2] = conversion[sliced_string[2]]


        # signs are always on the edges
        if (dim_code == "sign") or (dim_code == "duckie"):
            angle = [-(math.pi / 2), 0][random.randint(0, 1)]
        else:
            angle = random.uniform(-(math.pi / 2), 0)

        if (dim_code == "sign"):
            r = 1
        else:
            r = [0.25, 0.75][random.randint(0, 1)]


        if   ("E" == sliced_string[2]):  # Q2  |_
            angle += math.pi / 2
        elif ("N" == sliced_string[2]):  # Q3 _|
            angle += math.pi
        elif ("W" == sliced_string[2]):  # Q4  --|
            angle += 3 * (math.pi / 2)

        obj_x = round(math.cos(angle) * r, 2)
        obj_y = round(math.sin(angle) * r, 2)
        if ("N" == sliced_string[2]) or ("E" == sliced_string[2]):
            y += 1
        if ("N" == sliced_string[2]) or ("W" == sliced_string[2]):
            x += 1

        # this is a useful test to make sure curve rotation is correctly done:
        # OBJECT_LIST.append( ("cone", x, y, 0, 0.08, False) )

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
                cross_x = [0, 1]        # for duck crossing sign
                cross_y = [obj_y]
                cross_rotn = [270, 90]
            else:
                cross_y = [0, 1]
                cross_x = [obj_x]
                cross_rotn = [0, 180]
            if ((allowed(map, orig_x, orig_y, x + cross_x[0],  y + cross_y[0],  "sign")) and
                (allowed(map, orig_x, orig_y, x + cross_x[-1], y + cross_y[-1], "sign")) and
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

        # If an object overlaps onto driveable tiles on both sides,
        # it is too big to be placed.
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

        # recheck for diagonals
        # these variables represent object overlap, and will be used to decide if
        # the object must be shifted
        left = False
        right = False
        up = False
        down = False
        if ((obj_x + DIMS[dim_code][1]) > 1) and (orig_x < len(map[0]) - 1):
            right = True
        if ((obj_x - DIMS[dim_code][1]) < 0) and (orig_x > 0):
            left  = True
        if ((obj_y + DIMS[dim_code][1]) > 1) and (orig_y < len(map) - 1):
            down  = True
        if ((obj_y - DIMS[dim_code][1]) < 0) and (orig_y > 0):
            up    = True

        up_right   = False
        down_right = False
        up_left    = False
        down_left  = False
        # if there is overlap into up and right tiles, and the
        # up-right diagonal tile is driveable, this var is set to True
        if (
                (up and right) and not
                ((map[orig_y - 1][orig_x + 1]) == "grass" or
                 (map[orig_y - 1][orig_x + 1]) == "asphalt" or
                 (map[orig_y - 1][orig_x + 1]) == "floor")
        ):
            up_right = True
        if (
                (down and right) and not
                ((map[orig_y + 1][orig_x + 1]) == "grass" or
                 (map[orig_y + 1][orig_x + 1]) == "asphalt" or
                 (map[orig_y + 1][orig_x + 1]) == "floor")
        ):
            down_right = True
        if (
                (up and left) and not
                ((map[orig_y - 1][orig_x - 1]) == "grass" or
                 (map[orig_y - 1][orig_x - 1]) == "asphalt" or
                 (map[orig_y - 1][orig_x - 1]) == "floor")
        ):
            up_left = True
        if (
                (down and left) and not
                ((map[orig_y + 1][orig_x - 1]) == "grass" or
                 (map[orig_y + 1][orig_x - 1]) == "asphalt" or
                 (map[orig_y + 1][orig_x - 1]) == "floor")
        ):
            down_left = True
        # there may be a better way to shift obj rather than just disallowing the placement
        if (up_right or down_right or up_left or down_left):
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


def randomize_duck_heights():
    global OBJECT_LIST
    for i in range(0, len(OBJECT_LIST)):
        # element format: ( "kind", x, y, rotation, height, optional )
        # delete duckie, give it a new height, then reappend it
        if (OBJECT_LIST[i][0] == "duckie"):
            curr_element = tuple(OBJECT_LIST[i])
            OBJECT_LIST.remove(curr_element)
            curr_element = list(curr_element)
            h = 0
            # if random height is too tall or short, we regenerate
            while (h < 0.03) or (h > 0.05):
                h = round(random.gauss(0.04, 0.005), 4)

            curr_element[4] = h
            OBJECT_LIST.append(tuple(curr_element))


def print_objects():
    randomize_duck_heights()
    sys.stdout.write("objects:\n\n")
    for i in range(0, len(OBJECT_LIST)):
        sys.stdout.write("- kind: " + OBJECT_LIST[i][0] + "\n")
        sys.stdout.write("  pos: [" + str(OBJECT_LIST[i][1]) + ", " + str(OBJECT_LIST[i][2]) + "]\n")
        sys.stdout.write("  rotate: " + str(OBJECT_LIST[i][3] % 360) + "\n")
        sys.stdout.write("  height: " + str(OBJECT_LIST[i][4]) + "\n\n")
    sys.stdout.flush()


SIGN_IDS = {
    "sign_4_way_intersect": 8,
    "sign_T_intersect": 11,
    "sign_right_T_intersect": 9,
    "sign_left_T_intersect": 10,
    "sign_stop": 1,
    "sign_do_not_enter": 5,
    "sign_pedestrian": 12,
    "sign_t_light_ahead": 74,
    "sign_yield": 2,
    "sign_duck_crossing": 95,
    "sign_no_left_turn": 41,
    "sign_no_right_turn": 40,
    "sign_oneway_right": 42,
    "sign_oneway_left": 43
}

def write_signs():
    with open('sign_output.yaml', 'w+') as f2:
        f2.write("signs:\r\n")
        f2.write("\r\n")
        for i in range(0, len(OBJECT_LIST)):
            if ("sign" in OBJECT_LIST[i][0]) and (OBJECT_LIST[i][0] != "sign_blank"):
                f2.write("- kind: " + OBJECT_LIST[i][0] + "\r\n")
                # coordinates are converted from tile-lengths to metres
                f2.write("  pos: [" + str(round(float(OBJECT_LIST[i][1]) * 0.61, 2)) + ", " + str(round(float(OBJECT_LIST[i][2]) * 0.61)) + "]\r\n")
                f2.write("  rotate: " + str(OBJECT_LIST[i][3] % 360) + "\r\n")
                f2.write("  ID: " + str(SIGN_IDS[OBJECT_LIST[i][0]]) + "\r\n\r\n")



def write_objects():
    randomize_duck_heights()
    f.write("\r\n")
    f.write("objects:\r\n")
    f.write("\r\n")
    for i in range(0, len(OBJECT_LIST)):
        f.write("- kind: " + OBJECT_LIST[i][0] + "\r\n")
        f.write("  pos: [" + str(OBJECT_LIST[i][1]) + ", " + str(OBJECT_LIST[i][2]) + "]\r\n")
        f.write("  rotate: " + str(OBJECT_LIST[i][3] % 360) + "\r\n")
        f.write("  height: " + str(OBJECT_LIST[i][4]) + "\r\n\r\n")

    print("Objects generated and written to output.yaml")

#========================================= END =============================================
#===========================================================================================
#========================================= MAIN ============================================



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generates random map and places objects on it.\n \
             You MUST either enter a map file on which to generate objects with --map-name <file.yaml>,\n \
             or enter a height and width to generate a new map."  )
    parser.add_argument("--map-name", help="enter path of map file on which to place objects")
    parser.add_argument('--width', '-wd', type=int)
    parser.add_argument('--height', '-ht', type=int)
    parser.add_argument('--no-intersections', '-ni', action="store_true")
    parser.add_argument('--map-density', '-md', help="options: 'any', 'sparse', 'medium', 'dense'. \n \
                         Note: density not taken into account in maps under 8x8 in size")
    parser.add_argument('--no-border', '-nb', action="store_true")
    parser.add_argument('--side-objects', '-so', help="density of objects on non-driveable tiles \n \
                        options: 'empty', 'any', 'sparse', 'medium', 'dense'.")
    parser.add_argument("--road-objects", '-ro', help="density of objects on driveable tiles \n \
                        options: 'empty', 'any', 'sparse', 'medium', 'dense'.")
    parser.add_argument("--hard-mode", '-hard', action="store_true" )
    parser.add_argument("--sign-output", '-s', action="store_true", help="output a metric feature-based map in sign_output.yaml")
    parser.add_argument("--matrix-output", '-m', action="store_true",
                        help="output an adjacency matrix of the map")

    args = parser.parse_args()

    if (args.height < 3) and (args.height is not None):
        print("Height too small, please enter a height of 3 or greater.")
        sys.exit()
    if (args.width < 3) and (args.width is not None):
        print("Width too small, please enter a width of 3 or greater.")
        sys.exit()

    has_intersections = not args.no_intersections

    if (
            args.map_density == "any"    or
            args.map_density == "sparse" or
            args.map_density == "medium" or
            args.map_density == "dense"
    ):
        map_density = args.map_density
    else:
        map_density = "any"

    if (args.no_border):
        has_border = False
    else:
        has_border = True

    if (
            args.side_objects == "empty"  or
            args.side_objects == "any"    or
            args.side_objects == "sparse" or
            args.side_objects == "medium" or
            args.side_objects == "dense"
    ):
        side_objects = args.map_density
    else:
        side_objects = "medium"

    if (
            args.road_objects == "empty"  or
            args.road_objects == "any"    or
            args.road_objects == "sparse" or
            args.road_objects == "medium" or
            args.road_objects == "dense"
    ):
        road_objects = args.map_density
    else:
        road_objects = "empty"


    main(args.map_name, args.height, args.width, has_intersections, map_density, has_border,
        side_objects, road_objects, args.hard_mode, args.sign_output, args.matrix_output)