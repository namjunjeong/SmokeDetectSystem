from ultralytics import YOLO
import cv2

class Yolo_Utils_Class():
    def __init__(self):
        self.model = YOLO('yolov8n.pt')#define yolo model
        
    def yolo_box_data(self, pil_img, ind=1, save=False):
        result = self.model(pil_img)
        
        if save:
            plot_img = result[0].plot()
            cv2.imwrite(f'{str(ind)}.jpeg',plot_img)#save processed image
            
        return result[0].boxes.data.tolist()
    
    def yolo_img_data(self, pil_img):
        result = self.model(pil_img)
        return result[0].plot()