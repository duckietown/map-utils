# **Random generation of Duckietown maps**
___
Semi-randomly generates [Duckietown](http://duckietown.org/) maps to be used in the [Gym-Duckietown](https://github.com/duckietown/gym-duckietown).

## Introduction
This repository uses three python files to generate a random
map within the official [Duckietown Specifications](https://docs.duckietown.org/opmanual_duckietown/out/duckietown_specs.html) (section 2). The files are:

* ***map_output_beta_1.py*** : Outputs a generated map to output.yaml using the map format described in [Gym-Duckietown's README](https://github.com/duckietown/gym-duckietown/blob/master/README.md). It calls *map_gen_beta_1.py* to generate road system and it calls *populate_beta_1.py* to populate the map with objects.
* ***map_gen_beta_1.py*** : Generates a road system using a backtracking algorithm
according to the parameters entered in *map_output_beta_1*. This file creates an
undirected cyclic graph, which when exported to *map_output_beta_1* is translated
to 2D array of tiles selected from the following tile types:
>- empty
>- straight
>- curve_left
>- curve_right
>- 3way_left (3-way intersection)
>- 3way_right
>- 4way (4-way intersection)
>- asphalt
>- grass
>- floor (office floor)
>
>*(Taken from [Gym-Duckietown's README](https://github.com/duckietown/gym-duckietown/blob/master/README.md))*
* ***populate_beta_1.py (NOT YET WRITTEN)*** : Populates the map with objects selected from the following object types:

>- barrier
>- cone (traffic cone)
>- duckie
>- duckiebot (model of a Duckietown robot)
>- tree
>- house
>- truck (delivery-style truck)
>- bus
>- building (multi-floor building)
>- sign_blank (a blank sign post)
>
>*(Taken from [Gym-Duckietown's README](https://github.com/duckietown/gym-duckietown/blob/master/README.md))*



## Installation:
In order to run this program you must have a working installation of Python 3.5+.

## Usage:
This program can be run by entering the following in a terminal while in the map-utils directory:
```
./map_output_beta_1 <height> <width> --no_intersections --density <valid string> --no_border
```
### Breakdown of the parameters
Positional (required) arguments:
* `height` : an `int` describing the height of the map
    - height must be at least 3
* `width` : an `int` describing the width of the map
    - width must be at least 3

Optional arguments:
* `--no_intersections` or `-ni` : if specified, the map generated will have no intersections (AKA a *closed course*). Otherwise, intersections will be allowed.
* `--density` : specifies how densly packed the road network will be
    - valid input strings:
        - `"any"`
        - `"sparse"`
        - `"medium"`
        - `"dense"`
    - if nothing is inputted, or the string is invalid, the map will be of density `"any"`
    - if the map is under a size of 7x7, any density entered will be ignored
* `--no_border` or `-nb` : if specified, the map generated will not have a border when output. Otherwise, it will be output with a border of empty tiles (grass, floor, or asphalt, chosen at random).


## Troubleshooting
This program is in beta, so if you run into any bugs, please [open an issue](https://github.com/duckietown/map-utils/issues)

# Have fun generating!
