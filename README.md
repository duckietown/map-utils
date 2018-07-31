# **Random generation of Duckietown maps**

Semi-randomly generates [Duckietown](http://duckietown.org/) maps to be used in the [Gym-Duckietown](https://github.com/duckietown/gym-duckietown).

## Introduction
This repository uses two python files to generate a random
map within the official [Duckietown Specifications](https://docs.duckietown.org/opmanual_duckietown/out/duckietown_specs.html) (section 2).

#### Generation phases
1. Generation of the map by ***map_gen_beta_2.py*** : Generates a road system using a backtracking algorithm
according to the parameters entered in *map_output_beta_2* (terminal output shown):

<p align="center"><img src="images/small_terminal.png"></p>

* Note: in the terminal, each node is marked by its degree
* This file creates an
undirected cyclic graph, which when exported to *map_output_beta_2.py* is translated to a 2D array of tiles selected from the following tile types:

><p align="center"><img width="433" height="300" src="images/tiles.png"></p>
>
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

2. ***map_output_beta_2.py*** writes road network to yaml file *(output.yaml)* using the map format described in [Gym-Duckietown's README](https://github.com/duckietown/gym-duckietown/blob/master/README.md):

<p align="center"><img src="images/small_yaml.png"></p>

3. ***map_output_beta_2*** populates the map with objects

* Objects selected from the following object types:

>- barrier
>- cone (traffic cone)
>- duckie
>- duckiebot (model of a Duckietown robot)
>- tree
>- house
>- truck (delivery-style truck)
>- bus
>- building (multi-floor building)
>- sign (many types)
>
>*(Taken from [Gym-Duckietown's README](https://github.com/duckietown/gym-duckietown/blob/master/README.md))*

4. ***map_output_beta_2.py*** writes the objects that were generated to output.yaml


## Installation:

In order to run this program you must have a working installation of Python 3.5+. The output is meant to be used with the [gym-duckietown simulator](https://github.com/duckietown/gym-duckietown), which has its own set of dependencies.

## Usage:

This program can be run by entering the following in a terminal while in the map-utils directory:
```
./map_output_beta_1 <width> <height> --no_intersections --map_density <valid string> --no_border --obj_density <valid string> --road_objects
```

#### Breakdown of the parameters

Positional (required) arguments:
* `width` : an `int` describing the width of the map
    - width must be at least 3
* `height` : an `int` describing the height of the map
    - height must be at least 3

Optional arguments:
* `--no_intersections` or `-ni` : if specified, the map generated will have no intersections (AKA a *closed course*). Otherwise, intersections will be allowed.
* `--map_density` or `-md` : specifies how densely packed the road network will be
    - valid input strings:
        - `"any"` (default)
        - `"sparse"`
        - `"medium"`
        - `"dense"`
    - if nothing is inputted, or the string is invalid, the map will be of density `"any"`
    - if the map is under a size of 7x7, any density entered will be ignored
* `--no_border` or `-nb` : if specified, the map generated will not have a border when output. Otherwise, it will be output with a border of empty tiles (grass, floor, or asphalt, chosen at random).
* `--obj-density` or `-od` : specifies the density of objects to be placed on the map
    - valid input strings:
        - `"empty"` (default)
        - `"any"`
        - `"sparse"`
        - `"medium"`
        - `"dense"`
* `--road_objects` or `-ro` : if specified, the map generated will allow objects to be placed on the road (by default the roads are clear)
    - this will have no effect if *object density* is not specified, as it is *'empty'* by default

#### Examples

**Ex. 1**

```
./map_output_beta_2 7 5 --no_border --obj_density "medium" --road_objects
```
Outputs a map with dimensions 7x5 with no border medium object density including on roads:

**Terminal:**
<p align="center"><img src="images/ex1_map.png" alt="Terminal output"></p>


<details>
<summary><b>output.yaml:</b></summary>

 ```yaml
 tiles:
- [asphalt,       asphalt,       asphalt,       asphalt,       curve_right/N, straight/W,    curve_left/N]
- [curve_right/N, straight/W,    straight/W,    3way_right/E,  curve_left/E,  grass,         straight/N]
- [straight/N,    asphalt,       asphalt,       straight/N,    asphalt,       grass,         straight/N]
- [curve_right/W, curve_left/N,  asphalt,       straight/N,    asphalt,       curve_right/N, curve_left/E]
- [asphalt,       curve_right/W, straight/W,    3way_right/W,  straight/W,    curve_left/E,  asphalt]

objects:

- kind: sign_right_T_intersect
  pos: [4.05, 2.05]
  rotate: 180
  height: 0.18

- kind: sign_stop
  pos: [2.95, 2.05]
  rotate: 0
  height: 0.18

- kind: sign_stop
  pos: [4.05, 0.95]
  rotate: 180
  height: 0.18

- kind: sign_T_intersect
  pos: [4.15, 0.95]
  rotate: 270
  height: 0.18

- kind: sign_left_T_intersect
  pos: [2.95, 0.95]
  rotate: 0
  height: 0.18

- kind: sign_stop
  pos: [2.85, 0.95]
  rotate: 270
  height: 0.18

- kind: sign_right_T_intersect
  pos: [2.95, 3.95]
  rotate: 0
  height: 0.18

- kind: sign_stop
  pos: [4.05, 3.95]
  rotate: 180
  height: 0.18

- kind: sign_stop
  pos: [2.95, 5.05]
  rotate: 0
  height: 0.18

- kind: sign_left_T_intersect
  pos: [4.05, 5.05]
  rotate: 180
  height: 0.18

- kind: sign_left_T_intersect
  pos: [4.05, 5.05]
  rotate: 180
  height: 0.18

- kind: sign_stop
  pos: [4.15, 5.05]
  rotate: 90
  height: 0.18

- kind: truck
  pos: [2.31, 0.71]
  rotate: 264.61
  height: 0.2

- kind: building
  pos: [0.85, 0.47]
  rotate: 180
  height: 0.6

- kind: bus
  pos: [3.75, 2.61]
  rotate: 90
  height: 0.18

- kind: sign_pedestrian
  pos: [1.89, 2.67]
  rotate: 182.3
  height: 0.18

- kind: sign_do_not_enter
  pos: [6, 3]
  rotate: 90.0
  height: 0.18

- kind: sign_do_not_enter
  pos: [7.0, 3.0]
  rotate: 270.0
  height: 0.18

- kind: sign_yield
  pos: [1.69, 1]
  rotate: 0
  height: 0.18

- kind: sign_yield
  pos: [1.69, 2]
  rotate: 180
  height: 0.18

- kind: bus
  pos: [2.44, 1.75]
  rotate: 0
  height: 0.18
 ```
</details>

<br/>

**Simulator:**
<p align="center"><img width="400" height="284" src="images/ex1_sim.png"></p>

___

**Ex. 2**

```
./map_output_beta_2 10 10 --map_density "dense"
```
Outputs a *dense* map with dimensions 10x10 with no objects:

<p align="center"><img src="images/ex2_map.png" alt="Terminal output"></p>

<details>
<summary><b>output.yaml</b></summary>

```yaml

tiles:
- [asphalt,       asphalt,       asphalt,       asphalt,       asphalt,       asphalt,       asphalt,       asphalt,       asphalt,       asphalt,       asphalt,       asphalt]
- [asphalt,       curve_right/N, straight/W,    3way_right/E,  straight/W,    straight/W,    straight/W,    straight/W,    curve_left/N,  grass,         grass,         asphalt]
- [asphalt,       straight/N,    asphalt,       straight/N,    asphalt,       asphalt,       asphalt,       asphalt,       curve_right/W, curve_left/N,  grass,         asphalt]
- [asphalt,       3way_right/N,  straight/W,    4way,          straight/W,    straight/W,    curve_left/N,  asphalt,       asphalt,       straight/N,    grass,         asphalt]
- [asphalt,       straight/N,    asphalt,       straight/N,    grass,         grass,         straight/N,    asphalt,       asphalt,       curve_right/W, curve_left/N,  asphalt]
- [asphalt,       straight/N,    asphalt,       curve_right/W, curve_left/N,  grass,         curve_right/W, curve_left/N,  asphalt,       asphalt,       straight/N,    asphalt]
- [asphalt,       curve_right/W, curve_left/N,  grass,         curve_right/W, curve_left/N,  grass,         straight/N,    asphalt,       asphalt,       straight/N,    asphalt]
- [asphalt,       grass,         straight/N,    grass,         grass,         curve_right/W, straight/W,    curve_left/E,  asphalt,       asphalt,       straight/N,    asphalt]
- [asphalt,       grass,         curve_right/W, straight/W,    curve_left/N,  grass,         grass,         grass,         curve_right/N, straight/W,    curve_left/E,  asphalt]
- [asphalt,       grass,         grass,         grass,         curve_right/W, curve_left/N,  grass,         curve_right/N, curve_left/E,  grass,         grass,         asphalt]
- [asphalt,       grass,         grass,         grass,         grass,         curve_right/W, straight/W,    curve_left/E,  asphalt,       grass,         grass,         asphalt]
- [asphalt,       asphalt,       asphalt,       asphalt,       asphalt,       asphalt,       asphalt,       asphalt,       asphalt,       asphalt,       asphalt,       asphalt]
```
</details>

<br/>

**Simulator:**
<p align="center"><img width="400" height="284" src="images/ex2_sim.png"></p>

___

**Ex. 3**

```
./map_output_beta_2 5 5 --no_intersections --obj_density "sparse"
```
Outputs a 5x5 map with a border, and with no intersections and sparse object density, with none on the road:

<p align="center"><img src="images/ex3_map.png" alt="Terminal output"></p>

<details>
<summary><b>output.yaml</b></summary>

```yaml

tiles:
- [grass,         grass,         grass,         grass,         grass,         grass,         grass]
- [grass,         grass,         grass,         curve_right/N, straight/W,    curve_left/N,  grass]
- [grass,         grass,         curve_right/N, curve_left/E,  asphalt,       straight/N,    grass]
- [grass,         curve_right/N, curve_left/E,  asphalt,       asphalt,       straight/N,    grass]
- [grass,         straight/N,    asphalt,       curve_right/N, straight/W,    curve_left/E,  grass]
- [grass,         curve_right/W, straight/W,    curve_left/E,  grass,         grass,         grass]
- [grass,         grass,         grass,         grass,         grass,         grass,         grass]


objects:

- kind: house
  pos: [0.69, 6.22]
  rotate: 0
  height: 0.5

- kind: house
  pos: [3.0, 0.32]
  rotate: 270
  height: 0.5

- kind: sign_yield
  pos: [6.68, 0.95]
  rotate: 17.63
  height: 0.18

- kind: duckiebot
  pos: [2.18, 4.4]
  rotate: 16.69
  height: 0.1

- kind: tree
  pos: [4.17, 0.26]
  rotate: 86.16
  height: 0.25

- kind: duckie
  pos: [6.22, 4.9]
  rotate: 166.33
  height: 0.08

- kind: tree
  pos: [6.77, 3.89]
  rotate: 121.33
  height: 0.25

- kind: sign_t_light_ahead
  pos: [6.77, 3.15]
  rotate: 142.28
  height: 0.18

- kind: tree
  pos: [6.48, 4.11]
  rotate: 329.35
  height: 0.25
```
</details>

<br/>

**Simulator:**
<p align="center"><img width="400" height="284" src="images/ex3_sim.png"></p>

___

## Known bugs & problems

1. The *density* parameter does not scale well with size. It is currently calibrated to a 10x10 map. Due to the nature of smaller maps, where variation in density is very limited, any map under 7x7 in dimensions simply ignores any density entered, for the time being.
2. An invalid map was *once* found to be generated. This is to be dealt with at a future date as it is so rare.
3. Non-intersection signs do not appear on *clear road* maps

## Troubleshooting
This program is in beta, so if you run into any bugs, please [open an issue](https://github.com/duckietown/map-utils/issues)

# Have fun generating!
