from ultralytics import YOLO
import cv2

class Yolo_Utils_Class():
    def __init__(self, model_name):
        self.model = YOLO(model_name)#define yolo model
        
    def yolo_predict(self, pil_img, ind=1, with_image=False, save=False):
        result = self.model.predict(pil_img, verbose=False)
        plot_img = result[0].plot()
        data = result[0].boxes.data.tolist()
        
        if save:
            cv2.imwrite(f'{str(ind)}.jpeg',plot_img)#save processed image

        if with_image:
            return (plot_img, data)

        return data