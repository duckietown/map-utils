# July 10, 2018
# adamsigal on GitHub and in real life
# Part of the Duckietown project: https://www2.duckietown.org/
import random
import sys
import math
#========================= GLOBAL VARS / SETUP ================================
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
    #     min%   max%
    "any":    (14, 100),
    "sparse": (14, 18),
    "medium": (18, 23),
    "dense":  (23, 100)
}

#==============================================================================
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

        #print("original: ({}, {})".format(rand_x, rand_y))

        # "N" curve is defined as: _|_ ; turned 90 degrees clockwise subsequently
        positions = ["N", "E", "S", "W"]
        choice = positions[random.randint(0, len(positions) - 1)]
        #print("choice: {}".format(choice))

        if (rand_x<=1) and (choice != "E"):
            rand_x += 2 - rand_x
        elif (rand_x>=width-2) and (choice != "W"):
            rand_x -= 2 - ((width-1) - rand_x)

        if (rand_y<=1) and (choice != "S"):
            rand_y += 2 - rand_y
        elif (rand_y>=height-2) and (choice != "N"):
            rand_y -= 2 - ((height-1) - rand_y)
        #print("updated: ({}, {})".format(rand_x, rand_y))

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

        #print("original: ({}, {})".format(rand_x, rand_y))

        if (rand_x <= 1):
            rand_x += 2 - rand_x
        elif (rand_x >= width - 2):
            rand_x -= 2 - ((width-1) - rand_x)

        if (rand_y <= 2):
            rand_y += 2 - rand_y
        elif (rand_y >= height - 2):
            rand_y -= 2 - ((height-1) - rand_y)

        #print("random seed coordinates: ({}, {})".format(rand_x, rand_y))
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
            # print(m)
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


#==============================================================================
#================================= GROW =======================================
def grow():

    backtracked = False
    ctr = 0
    while (len(ONES) > 0) and (ctr < 10000):
        ctr += 1
        # If the last step created a deg 3 node when the map
        # is to have NO INTERSECTIONS, then we backtrack
        if (not HAS_INTERSECTIONS) and (len(scan_for_degx(3)) > 0):
            # if map is well covered, trimming is likely to produce a good map
            if (check_coverage(len(MAP), len(MAP[0]))):
                trim()
                #print("\n")
                continue
            # otherwise, backtrack to find better solution
            else:
                backtrack()
                backtracked = True
                #print("\n")
                continue

        if (backtracked):
            if(len(STACK)==0):
                ascii_map()
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
                    #print("\n")
                    continue
        else:
            next = MAP[ONES[-1][1]][ONES[-1][0]]
            rel_dirs = find_rel_dirs(find_leading_connection(next))
            options_left = list(POSSIBLE_STEPS)

        while (len(options_left) > 0):
            rand_step = options_left[random.randint(0, len(options_left)-1)]
            if (is_safe(next,rand_step, rel_dirs)):
                #print("Taking a step: {}".format(rand_step))
                options_left.remove(rand_step)
                STACK.append([next, rand_step, rel_dirs, options_left])
                prev_cxns = step(next, rand_step, rel_dirs)
                STACK[-1].append(prev_cxns)
                break
            else:
                #print("No legal steps possible")
                options_left.remove(rand_step)
                if (len(options_left) == 0):
                    if (STACK[-1][1] == ""):
                        raise ValueError("ERROR: Trying to backtrack from NO STEP")
                    else:
                        backtrack()
                        #print("ONES after backtrack: {}".format(ONES))
                        backtracked = True
            sys.stdout.flush()
        #print("\n")

    # if generation has taken more than 2 seconds, we "trim" the network;
    # remove elements of ONES until map is valid
    if (len(ONES) > 0):
        trim()




#==============================================================================
#============================ STEP ALGORITHMS =================================
# backtracks: pops last move from STACK and undoes last step
def backtrack():
    top_stack = STACK[-1]
    node = top_stack[0]
    last_step = top_stack[1]
    rel_dirs = top_stack[2]
    prev_cxns = top_stack[4]
    #print("backtracking from last step: {} ({}, {})".format(last_step, node.x, node.y))

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
            ascii_map()
            print("ONES: {}".format(ONES))

            rel_dirs = find_rel_dirs(find_leading_connection(curr_node))
            print(rel_dirs)
            curr_node.disconnect(rel_dirs["b"])
            new_len = len(ONES)

        if (new_len>old_len):
            raise ValueError("Somehow trim made us gain ONES")




#==============================================================================
#======================== SAFETY & CHECK ALGORITHMS ===========================
# LOGIC BEHIND "CHECK" FUNCTIONS IS EXPLAINED IN check_fxn_diagrams-v2.png

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
            # TODO: if consolidated, connect with curve (if in corner)
            return True

        # if on the left edge (with space in front)
        elif((node.neighbours[rel_dirs["l"]] is None) and   # 1.3
              node.neighbours[rel_dirs["r"]].deg() == 0):
            if (node.neighbours[rel_dirs["f"]].connected[rel_dirs["f"]]):   #1.3.1
                return True
            else:   # 1.3.2
                # we now allocate variables for code legibility
                # TODO: change if this affects complexity too much
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
                # TODO: change if this affects complexity too much
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
            if (node.neighbours[rel_dirs["f"]].connected[rel_dirs["f"]]): # 1.5.1
                return True
            else: #1.5.2
                # we now allocate variables for code legibility
                # TODO: change if this affects complexity too much
                a = node.neighbours[rel_dirs["f"]].neighbours[rel_dirs["f"]].neighbours[rel_dirs["l"]]
                b = node.neighbours[rel_dirs["f"]].neighbours[rel_dirs["f"]]
                c = node.neighbours[rel_dirs["f"]].neighbours[rel_dirs["f"]].neighbours[rel_dirs["r"]]
                d = node.neighbours[rel_dirs["f"]].neighbours[rel_dirs["l"]]
                e = node.neighbours[rel_dirs["f"]].neighbours[rel_dirs["r"]]
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
            print(node.neighbours[rel_dirs["l"]].deg())
            node.disconnect(rel_dirs["l"])
            print(node.neighbours[rel_dirs["r"]].deg())
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

# =============================================================================
# ============================= NODE CLASS ====================================
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



# =============================================================================
# ================================ MAIN =======================================

def main():

    create_map(10, 10, True, "any")


if __name__ == "__main__":
    main()
