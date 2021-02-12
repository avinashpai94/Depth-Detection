import numpy as np
import argparse
import cv2
import glob
import os

class DisparityMap(object):

    def __init__(self, ifile_path, ofile_path, algorithm, display_mode):
        """
        Rectifies and remaps the first image pair from the stereo cameras.

        Parameters
        ----------
        ifile_path: filepath containing stereocamera images.
            Filepath must contain 2 folders 'LEFT' and 'RIGHT
            e.g. for '/sample/path/LEFT' and 'sample/path/RIGHT',
            filepath should be '/sample/path/'

        ofile_path: The output file path at which the rectified images
        will be written to.

        Algorithm : Set to 1 for Block Matching (BM), Set to 2 for
        Semi Global Block Matching (SGBM)

        Display Mode: Set to 1 to display disparity map, set to 0 to disable
        display. (Useful if automating the process)
        """
        self.d_map = self._mapout(ifile_path, ofile_path, algorithm, display_mode)

    def _mapout(self, ifile_path, ofile_path, algorithm, display_mode):

        ofile_path = dir_path = os.path.dirname(os.path.realpath(__file__)) + '/'+ofile_path

        type, disparity_map = 0, 0

        images_right = glob.glob(ifile_path + 'RIGHT/*.jpg')
        images_left = glob.glob(ifile_path + 'LEFT/*.jpg')
        if(not images_right):
            images_right = glob.glob(ifile_path + 'RIGHT/*.JPG')
        if(not images_left):
            images_left = glob.glob(ifile_path + 'LEFT/*.JPG')
        images_right.sort()
        images_left.sort()

        file_table = []

        #code to pick and display only image names
        for file in images_right:
            _, file = os.path.split(file)
            file = file[2:-4];
            file_table.append(file)

        print('Num       Name')
        for i, name in zip(range(len(file_table)), file_table):
            print(str(i+1)+" ....... "+name)

        pairnum = int(input('Enter File Number\n')) - 1

        try: #sometimes pictures are saved as .jpg or .JPG
            imgl = cv2.imread(images_left[pairnum])
            imgr = cv2.imread(images_right[pairnum]) # add to later
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

        x = images_left[pairnum].split('/')
        imgname = x[-1]

        imgl = cv2.cvtColor(imgl, cv2.COLOR_BGR2GRAY)
        imgr = cv2.cvtColor(imgr, cv2.COLOR_BGR2GRAY)

        height, width = imgl.shape[:2]

        focal_length = 0

        '''
        Picks up Focal length from label, if focal length doesn't exist or if label doesn't exist
        '''
        lbl_name = images_left[pairnum].split('/')[2].split('.')[0] +'.lbl'
        lbl_path = ifile_path+'LEFT/'+lbl_name
        if os.path.isfile(lbl_path):
            f = open(lbl_path, 'r')
            lines = f.readlines()
            for x in lines:
                line = x.split(':')
                if(line[0] == 'f'):
                    focal_length = int(line[1].strip().split('.')[0]) #get focal length as an integer from lines
                    break

        if not focal_length:
            try:
                focal_length = int(os.environ["FOCAL_LENGTH"])
            except KeyError as e:
                focal_length = 28

        try:
            base_length = int(os.environ["BASE_LENGTH"])
        except Exception as e:
            base_length = 250

        '''
        Disparity range relies on distance from camera to object of
        interest. objects that are closer to camera needs greater
        disparity range. Increasing BlockSize helps for images with little texture.
        '''

        if algorithm == '1':
            '''
            Stereo BM Algorithm
            '''

            # Change according to Opencv verif(not images_right):
            images_right = glob.glob(ifile_path + 'RIGHT/*.JPG')
            if(not images_left):
                images_left = glob.glob(ifile_path + 'LEFT/*.JPG')
            # stereoBM = cv2.StereoBM_create(preset = 0, ndisparities = 80,
            #         SADWindowSize = 5)

            stereoBM = cv2.StereoBM_create(numDisparities = 80, blockSize = 31)

            print('BM Initialized')
            disparityBM = stereoBM.compute(imgl, imgr)
            print('Disparity Computed')

            disparityBM = cv2.normalize(disparityBM, disparityBM, alpha = 0,
                    beta = 255, norm_type = cv2.NORM_MINMAX, dtype = cv2.CV_8U)


            '''
            On adding new algorithms, append the below two lines to the if case and change accordingly
            '''
            type = 'BM'
            disparity_map = disparityBM


        elif algorithm == '2':
            '''
            Stereo SGBM Algorithm
            '''

            # Change according to Opencv version

            # stereoSGBM = cv2.StereoSGBM_create(minDisparity = -16, numDisparities
            #         = 112, SADWindowSize = 7, P1 = 600, P2 = 2400,
            #         disp12MaxDiff = 1, preFilterCap = 16, uniquenessRatio = 1,
            #         speckleWindowSize = 100, speckleRange
            #         = 20, fullDP = False)

            stereoSGBM = cv2.StereoSGBM_create(minDisparity = 12, numDisparities
                            = 144, P1 = 600, P2 = 2400,
                            disp12MaxDiff = 1, preFilterCap = 16, uniquenessRatio = 1,
                            speckleWindowSize = 150, speckleRange
                            = 20, mode = 1)

            print('SGBM Initialized.')
            disparitySGBM = stereoSGBM.compute(imgl, imgr)
            print('Disparity Computed.')
            disparitySGBM = cv2.normalize(disparitySGBM, disparitySGBM, alpha =0
                    ,beta = 255,norm_type = cv2.NORM_MINMAX,dtype =  cv2.CV_8U)

            '''
            On adding new algorithms, append the below two lines to the if case and change accordingly
            '''
            type = 'SGBM'
            disparity_map = disparitySGBM


        '''
        Computing Depth map from calculated disparity map

        '''

        with np.errstate(divide='ignore'):
            depth_map = base_length*focal_length/disparity_map

        '''
        Folder Creations for disparity and depth _map
        Set variable ofile_path to base folder path. Code will create save folder based on ofile_path given
        Code below creates BM, SGBM Folders based on session data
        '''

        print('Writing Files...')

        '''
        Create save folder
        '''
        if not os.path.exists(ofile_path):
            os.makedirs(ofile_path)

        '''
        Create Session folder
        '''
        ofile_path += imgname[2:-4] #get session name from image name
        if not os.path.exists(ofile_path):
            os.makedirs(ofile_path)

        '''
        Create type folder
        '''
        ofile_path+= '/'+type+'/'
        if not os.path.exists(ofile_path):
            os.makedirs(ofile_path)

        #write image to path
        img_path = ofile_path + imgname.replace('L', type)
        if not cv2.imwrite(img_path, disparity_map):
            raise Exception("Could not write image")

        #write disparity csv to path
        disp_path = ofile_path + imgname.replace('L', 'disp'+type)
        disp_path = disp_path.replace('.jpg', '.csv')
        np.savetxt(disp_path, disparity_map, fmt = "%f", delimiter = ",")


        #write depth csv to path
        dept_path = ofile_path + imgname.replace('L', 'dept'+type)
        dept_path = dept_path.replace('.jpg', '.csv')
        np.savetxt(dept_path, depth_map, fmt = "%f", delimiter = ",")

        print('Files written.')

        '''
        Display Mode : Set display_mode = 1 to enable
        '''
        if display_mode == '1':
            cv2.namedWindow('Image_'+type, cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Image_'+type, height, width)
            cv2.imshow('Image_'+type, disparitySGBM)
            cv2.waitKey(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('ifile_path', help = 'Input Filepath')
    parser.add_argument('ofile_path', help = 'Output Filepath')
    parser.add_argument('algorithm', default = '2', help = 'Algorithm: BM = 1, SGBM = 2')
    parser.add_argument('display_mode', default = '0', help = 'Display: 1/0')
    args = parser.parse_args()
    DisparityMap(args.ifile_path, args.ofile_path, args.algorithm, args.display_mode)
