# July 10, 2018
# adamsigal on GitHub and in real life
# Part of the Duckietown project: https://www2.duckietown.org/
import sys
import random
import map_gen_beta_1
import argparse

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


def main(height, width, has_intersections, density, has_border):
    f = open("output.yaml","w+")
    f.write("tiles:\r\n")

    # ======================= write tile grid to file ==========================
    tile_grid = gen_tile_grid(height, width, has_intersections, density)

    border_empty = EMPTY_TYPES[random.randint(0, len(EMPTY_TYPES)-1)]
    tile_grid = define_inner_empties(height, width, tile_grid)

    x_len = len(tile_grid[0])
    if (has_border):
        y_len = len(tile_grid) + 2
    else:
        y_len = len(tile_grid)

    for j in range(0, y_len):
        # top border
        if (has_border) and (j == 0):
            f.write("- [")
            for r in range(0, x_len+2):
                f.write(border_empty)
                if (r < x_len+1):
                    if (r == 0):
                        f.write(", ")
                    else:
                        f.write(",")
                        for s in range(0, (14 - len(border_empty))):
                            f.write(" ")
            f.write("]\r\n")
            continue

        # bottom border
        if (has_border) and (j == y_len-1):
            f.write("- [")
            for r in range(0, x_len+2):
                f.write(border_empty)
                if (r < x_len+1):
                    if (r == 0):
                        f.write(", ")
                    else:
                        f.write(",")
                        for s in range(0, (14 - len(border_empty))):
                            f.write(" ")
            f.write("]\r\n")
            continue

        f.write("- [")
        for i in range(0, x_len):
            if (has_border):
                local_j = j-1
            else:
                local_j = j

            if (has_border) and (i == 0):
                f.write(border_empty + ", ")

            if tile_grid[local_j][i] == "":
                raise ValueError("Undefined tile at coordinates: ({}, {}".format(i, local_j))
            else:
                f.write(tile_grid[local_j][i])

            # every element followed by "," unless it is last element
            if (i < x_len-1):
                f.write(",")
                for s in range (0, (14-len(tile_grid[local_j][i]))):
                    f.write(" ")
            elif (i == x_len-1) and (has_border):
                f.write(",")
                for s in range(0, (14 - len(tile_grid[local_j][i]))):
                    f.write(" ")
                f.write(border_empty)
        f.write("]\r\n")


#===========================================================================
#=============== place objects on grid (write to file) =====================

    f.close()


# creates grid that fills all non-manually decided tiles with semi-random tiles
# writes grid to output.yaml
# returns grid, in case needed
def gen_tile_grid(height, width, has_intersections, density):
    tile_grid = [["" for x in range(width)] for y in range(height)]
    try:
        node_map = map_gen_beta_1.create_map(height, width, has_intersections, density)
    except:
        raise ValueError("There was a problem generating the map")

    for j in range(0, height):
        for i in range(0, width):
            tile_grid[j][i] = TILE_DICTIONARY[frozenset(node_map[j][i].connected.items())]

    return tile_grid


# defines all neighbouring empty tiles to be the same type, at random
def define_inner_empties(height, width, tile_grid):
    for j in range(0, height):
        for i in range(0, width):
           if (tile_grid[j][i] == "empty"):
                groups_type = EMPTY_TYPES[random.randint(0, len(EMPTY_TYPES)-1)]
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate random map using height, \
    width, no_intersections (bool) (optional), density string (optional), no_border (bool) (optional)')
    parser.add_argument('height', type=int)
    parser.add_argument('width', type=int)
    parser.add_argument('--no_intersections', '-ni', action="store_true")
    parser.add_argument('--density', help="options: 'any', 'sparse', 'medium', 'dense'. \n \
                         Note: density not taken into account in maps under 8x8 in size")
    parser.add_argument('--no_border', '-nb', action="store_true")

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

    if (args.density == "any" or
        args.density == "sparse" or
        args.density == "medium" or
        args.density == "dense"):
        density = args.density
    else:
        density = "any"

    if (args.no_border):
        has_border = False
    else:
        has_border = True

    main(args.height, args.width, has_intersections, density, has_border)