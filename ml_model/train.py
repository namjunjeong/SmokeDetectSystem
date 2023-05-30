from ultralytics import YOLO

if __name__ == '__main__':
    # Load a model
    model = YOLO("yolov8s.pt")
    
    # Use the model
    model.train(data="/local_datasets/Smoking-Detection-5/data.yaml", epochs=100, lrf=0.001, name='v8s-lrf-0.001')  # train the model
    metrics = model.val()  # evaluate model performance on the validation set
    success = model.export(format="onnx")  # export the model to ONNX format
