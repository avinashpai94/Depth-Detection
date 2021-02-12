# Disparity and Depth Map generation

Generates disparity map and depth map from a rectified image pair directly captured from raspberry pi.

## External Libraries used: 
numpy, glob, argparse, opencv-python

## Files used:
Disparity_map_dist_edit.py, image_rectify_dist_edit.py, camera_calibrate.py

## How to use
1. Capture a stereoscopic image pair.
![left_image](https://github.com/avinashpai94/Depth-Detection/blob/main/Working%20Example%20of%20Disparity%20Code/session_056_18052019/LEFT/L_056_0157.JPG)
           <p align="center">Stereoscopic Image (Left Image)</p>


2. Export HEIGHT_NUM, and WIDTH_NUM which are number of squares on the checkerboard. Rectification will not work without these environment variables.
(Make sure you count inner black corners around the height and width, the above image is of 19 x14 dimensions)

For example, if the images are going to be calibrated using the checkboard like the one above, we need to set the HEIGHT_NUM and WIDTH_NUM to 19 and 14 using the following commands in the terminal.
```
				export HEIGHT_NUM=19
				export WIDTH_NUM=14
```
Note: Interchanging the values of HEIGHT_NUM and WIDTH_NUM will not affect the calibration process.
 
3. Rectify the Image pair using the image_rectify_dist_edit.py. The Image pair file path needs to contain the folders LEFT and RIGHT, each with at least 10-12 stereo images to get a successful calibration.

This script takes two arguments. Both paths must be from the script path. 
Input Folder
This folder must contain LEFT and RIGHT folder, which consist of minimum 10 images each.
Output Folder
This folder will contain the rectified image pairs in LEFT and RIGHT directories. The folder will be created if it doesn’t exist
```
Example:
$ python image_rectify_dist_edit.py /path_to_input_folder /path_to_output_folder
```

![rectified_image](https://github.com/avinashpai94/Depth-Detection/blob/main/Working%20Example%20of%20Disparity%20Code/pics/LEFT/L_056_0.jpg)

<p align="center">Rectified Output (Left Image)</p>



4. Export environment variables FOCAL_LENGTH, and BASE_LENGTH into the terminal appropriately. Defaulted to 28, and 250 respectively (in mm). (Disparity map generation overrides environment variable with focal length from label if it exists)
```
				export FOCAL_LENGTH=28
				export BASE_LENGTH=250
```

5. Run Disparity map generation script disparity_map_dist_edit.py
This script takes 4 arguments, in order, as follows. Both paths must be from the script path. 
Input Folder
This folder must contain image pairs recorded in session folders. Each session folder will have a left and right image folder which contains one half of the pair each.
Output Folder
This folder will be the path to which the disparity map, and depth map would be saved. (Disparity Map as an image, Disparity Map as a CSV, and Depth map as a CSV will be saved).
Algorithm
Setting this argument to 1 will trigger the Stereo BM algorithm, 2 will trigger Stereo SGBM algorithm


### Output Mode
1 will trigger the script to open an image of the output. 0 otherwise. Use 0 while automating to prevent multiple windows opening.

```
Example:
$ python disparity_map_dist_edit.py /path_to_rectified_images /output_path algorithm_value display_mode 
```

<p align="center">Disparity Map Output (SGBM)</p>

![depthSGBM](https://github.com/avinashpai94/Depth-Detection/blob/main/Working%20Example%20of%20Disparity%20Code/056_0/SGBM/SGBM_056_0.jpg)


## Notes and Observations

### Modes
The stereosgbm algorithm takes an additional argument to denote type of mode.
The modes are as follows; These arguments should be changed within the code.

| Value | Mode |
| :---: | :---: | 
| 0 | MODE_SGBM |
| 1 | MODE_HH |
| 2 | MODE_SGBM_3WAY |
| 3 | MODE_HH4 |

Mode 0 is default; this is a single pass algorithm which considers only 5 directions instead of 8.
Mode 1 is a 2 pass dynamic programming algorithm which will consume more bytes. O(W*H*numDisparities)

It was found that Mode 1 would provide better results at the cost of more computing space but there was no documentation found on mode 2 or 3. Mode 1 was also found to be empirically better than Mode 2 or 3. 

### Continuous Surface
The image rectification algorithm was found to create weird results when a continuous surface such as a wall was present at various depths. 

### Dimensions of Checkerboard
The dimensions of the checkerboard play a role in image rectification. The bigger the dimension, the better the results are. 

The dimensions should be rectangular, i.e. there should be a considerable difference in number of horizontal black corners vs number of vertical black corners (HEIGHT_NUM vs WIDTH_NUM). The checkerboards that were tested were 19 x 14 and 9 x 6. The 19 x 14 board was found to have better results. 


### numDisparities vs minDisparity
numDisparities: Maximum disparity minus minimum disparity. The value is always greater than zero. In the current implementation, this parameter must be divisible by 16. 
minDisparity: Minimum possible disparity value. Normally, it is zero but sometimes rectification algorithms can shift images, so this parameter needs to be adjusted accordingly.

After a trial and error of setting value of numDisparities between 64 to 256, and minDisparity between 8-64, it was found that a value of 144 vs 12 was giving the best result.
Setting minDisparity = 12, and varying numDisp between 64-256.
Setting numDisp = 144, and varying minDisparities between 8-64.

## Future Work
*Implement more stereo matching algorithms and see how they differ in output.
*While rectifying the image, the exif data is lost. This is the reason why we need to export focal length before running the disparity code. Implement a function to save the exif data while rectifying the image, and use the saved focal length to get the disparity and depth map. This is temporarily solved by copying the label to the rectified image folder.


## References
1. Find Chessboard corners
https://docs.opencv.org/2.4/modules/calib3d/doc/camera_calibration_and_3d_reconstruction.html

2. StereoSGBMMatching
https://docs.opencv.org/3.4/d2/d85/classcv_1_1StereoSGBM.html
	
