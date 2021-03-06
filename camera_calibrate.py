import numpy as np
import cv2
import glob
import argparse
import os
import sys


class StereoCalibration(object):
    def __init__(self, filepath):
        # termination criteria
        self.criteria = (cv2.TERM_CRITERIA_EPS +
                         cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        self.criteria_cal = (cv2.TERM_CRITERIA_EPS +
                             cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-5)
        try:
            self.cdimsh = int(os.environ["HEIGHT_NUM"])
        except KeyError as e:
            print('Error. Height not set.')
            sys.exit()
        try:
            self.cdimsw = int(os.environ["WIDTH_NUM"])
        except KeyError as e:
            print('Error. Width not set.')
            sys.exit()

        # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
        self.objp = np.zeros((self.cdimsh * self.cdimsw, 3), np.float32)
        self.objp[:, :2] = np.mgrid[0:self.cdimsh, 0:self.cdimsw].T.reshape(-1, 2)

        # Arrays to store object points and image points from all the images.
        self.objpoints = []  # 3d point in real world space
        self.imgpoints_l = []  # 2d points in image plane.
        self.imgpoints_r = []  # 2d points in image plane.

        self.cal_path = filepath
        self.camera_model = self._read_images(self.cal_path)

    def _read_images(self, cal_path):
        """
        It reads images and find checkerboard patterns in it.

        Returns:
        camera_model: dict
            A dictionary containing stereo camera model. Intrinsic and
            Extrinsic parameters.
        """
        images_right = glob.glob(cal_path + 'RIGHT/*.jpg')
        images_left = glob.glob(cal_path + 'LEFT/*.jpg')
        if(not images_right):
            images_right = glob.glob(cal_path + 'RIGHT/*.JPG')
        if(not images_left):
            images_left = glob.glob(cal_path + 'LEFT/*.JPG')
        images_left.sort()
        images_right.sort()

        print('Starting find')
        for i, fname in enumerate(images_right):
            img_l = cv2.imread(images_left[i])
            img_r = cv2.imread(images_right[i])


            h_l, w_l = img_l.shape[:2]
            h_r, w_r = img_r.shape[:2]

            gray_l = cv2.cvtColor(img_l, cv2.COLOR_BGR2GRAY)
            gray_r = cv2.cvtColor(img_r, cv2.COLOR_BGR2GRAY)

            '''
            #flags for cv2.findChessboardCorners
            flag = 0
            flag |= cv2.CALIB_CB_ADAPTIVE_THRESH
            flag |= cv2.CALIB_CB_FILTER_QUADS
            '''

            # Find the chess board corners
            ret_l, corners_l = cv2.findChessboardCorners(
                gray_l, (self.cdimsh, self.cdimsw), None)
            # either flag or None for last argument
            ret_r, corners_r = cv2.findChessboardCorners(
                gray_r, (self.cdimsh, self.cdimsw), None)

            print('Image: ', i + 1, '/', len(images_left))
            print(ret_l, ret_r)
            # If found, add object points, image points (after refining them)

            if ret_l is True and ret_r is True:
                self.objpoints.append(self.objp)
                rt = cv2.cornerSubPix(gray_l, corners_l, (11, 11),
                                      (-1, -1), self.criteria)
                self.imgpoints_l.append(corners_l)

                # Draw and display the corners
                ret_l = cv2.drawChessboardCorners(
                    img_l, (self.cdimsh, self.cdimsw), corners_l, ret_l)

                rt = cv2.cornerSubPix(
                    gray_r, corners_r, (11, 11), (-1, -1), self.criteria)
                self.imgpoints_r.append(corners_r)

                # Draw and display the corners
                ret_r = cv2.drawChessboardCorners(
                    img_r, (self.cdimsh, self.cdimsw), corners_r, ret_r)

            img_shape = gray_l.shape[::-1]

        rt, self.M1, self.d1, self.r1, self.t1 = cv2.calibrateCamera(
            self.objpoints, self.imgpoints_l,
            img_shape, None, None)
        rt, self.M2, self.d2, self.r2, self.t2 = cv2.calibrateCamera(
            self.objpoints, self.imgpoints_r,
            img_shape, None, None)

        return self._stereo_calibrate(img_shape)

    def _stereo_calibrate(self, dims):
        """
        It performas stereo calibration and makes dictionary of stereo
        camera calibration model parameters.

        Returns:
        camera_model: dict
        A dictionary containing stereo camera model parameters.
        """
        flags = 0
        flags |= cv2.CALIB_FIX_INTRINSIC
        # flags |= cv2.CALIB_FIX_PRINCIPAL_POINT
        flags |= cv2.CALIB_USE_INTRINSIC_GUESS
        flags |= cv2.CALIB_FIX_FOCAL_LENGTH
        # flags |= cv2.CALIB_FIX_ASPECT_RATIO
        flags |= cv2.CALIB_ZERO_TANGENT_DIST
        # flags |= cv2.CALIB_RATIONAL_MODEL
        # flags |= cv2.CALIB_SAME_FOCAL_LENGTH
        # flags |= cv2.CALIB_FIX_K3
        # flags |= cv2.CALIB_FIX_K4
        # flags |= cv2.CALIB_FIX_K5

        stereocalib_criteria = (
            cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS, 100, 1e-5)

        ret, M1, d1, M2, d2, R, T, E, F = cv2.stereoCalibrate(
            self.objpoints, self.imgpoints_l,
            self.imgpoints_r, self.M1, self.d1, self.M2,
            self.d2, dims, criteria=stereocalib_criteria, flags=flags)
        # make sure to move around args according to opencv version

        rot_left, _ = cv2.Rodrigues(self.r1[0])
        rot_right, _ = cv2.Rodrigues(self.r2[0])

        R1, R2, P1, P2, Q, validPixROI1, validPixROI2S = cv2.stereoRectify(
            M1, d1, M2, d2, dims, R, T, flags=0, alpha=0)

        mapLx, mapLy = cv2.initUndistortRectifyMap(
            M1, d1, R1, P1, dims, m1type=cv2.CV_32FC1)
        mapRx, mapRy = cv2.initUndistortRectifyMap(
            M2, d2, R2, P2, dims, m1type=cv2.CV_32FC1)

        camera_model = dict([
            ('M1', M1), ('M2', M2), ('dist1', d1),
            ('dist2', d2), ('rot_left', rot_left),
            ('rot_right', rot_right), ('R', R), ('T', T),
            ('E', E), ('F', F), ('mapLx', mapLx), ('mapLy', mapLy),
            ('mapRx', mapRx), ('mapRy', mapRy), ('R1', R1), ('R2', R2),
            ('P1', P1), ('P2', P2), ('dims', dims)])

        return camera_model


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filepath', help='String Filepath')
    args = parser.parse_args()
    cal_data = StereoCalibration(args.filepath)
