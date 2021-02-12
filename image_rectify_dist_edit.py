from camera_calibrate import StereoCalibration
import numpy as np
import argparse
import cv2
import glob
import os
import shutil


class RectifyMap(object):
    def __init__(self, ifile_path, ofile_path):
        """
        Rectifies and remaps the first image pair from the stereo cameras.

        Parameters
        ----------
        ifile_path: filepath containing stereocamera images.
            Filepath must contain 2 folders 'LEFT' and 'RIGHT
            e.g. for '/sample/path/LEFT' and 'sample/path/RIGHT',
            filepath should be '/sample/path/'

        ofile_path: The output file path at which the rectified images
        will be written to. This filepath will contain two folders LEFT
        and RIGHT. The program will create the path if the folders don't
        exist.
        """
        print('Creating Stereo Camera Model...')
        self._cal = StereoCalibration(ifile_path)
        print('Calibration Performed...')
        self.r_image = self._mapout(ifile_path, ofile_path)


    def _mapout(self, ifile_path, ofile_path):
        ofile_path = dir_path = os.path.dirname(os.path.realpath(__file__)) + '/'+ofile_path
        x = ifile_path.split('_')
        print(x)
        sessnum = x[1]
        images_right = glob.glob(ifile_path + 'RIGHT/*.jpg')
        images_left = glob.glob(ifile_path + 'LEFT/*.jpg')
        images_right.sort()
        images_left.sort()
        pairnum = 0

        try:
            imgl = cv2.imread(images_left[pairnum])#run the rectifications on first image in the checkerboard dir
            imgr = cv2.imread(images_right[pairnum])
        except IndexError:
            if(not images_right):
                images_right = glob.glob(ifile_path + 'RIGHT/*.JPG')
            if(not images_left):
                images_left = glob.glob(ifile_path + 'LEFT/*.JPG')
            images_right.sort()
            images_left.sort()
            try:
                imgl = cv2.imread(images_left[pairnum])
                imgr = cv2.imread(images_right[pairnum])
            except IndexError:
                print('wrong path or wrong pairnum chosen in code')



        cal = self._cal.camera_model #get the camera_model dict from camera_calibrate.py

        finall= cv2.remap(imgl, cal['mapLx'], cal['mapLy'], interpolation = cv2.INTER_LINEAR)
        finalr = cv2.remap(imgr, cal['mapRx'], cal['mapRy'], interpolation = cv2.INTER_LINEAR)

        '''
        Create save folder
        '''
        if not os.path.exists(ofile_path):
            os.makedirs(ofile_path)

        '''
        Create LEFT and RIGHT folder
        '''
        left_path = ofile_path + 'LEFT/'

        if not os.path.exists(left_path):
            os.makedirs(left_path)

        right_path = ofile_path + 'RIGHT/'
        if not os.path.exists(right_path):
            os.makedirs(right_path)

        '''
        Write left and right images to left_path and right_path
        Write label to left path
        '''
        lbl_path = left_path + 'L_'+str(sessnum)+'_'+str(pairnum)+'.lbl'
        left_path += 'L_'+str(sessnum)+'_'+str(pairnum)+'.jpg'
        if not cv2.imwrite(left_path, finall):
            raise Exception('Could not write LEFT image')

        right_path += 'R_'+str(sessnum)+'_'+str(pairnum)+'.jpg'
        if not cv2.imwrite(right_path, finalr):
            raise Exception('Could not write RIGHT image')

        #Copy lbl to left directory of output folder | To get focal length during disparity calculation
        lbl_name = images_left[pairnum].split('/')[2].split('.')[0] +'.lbl'
        shutil.copy2(ifile_path+'LEFT/'+lbl_name, lbl_path)

        print('Images have been written to '+ofile_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('ifile_path', help='String Filepath')
    parser.add_argument('ofile_path', help='String Filepath')
    args = parser.parse_args()
    RectifyMap(args.ifile_path, args.ofile_path)
