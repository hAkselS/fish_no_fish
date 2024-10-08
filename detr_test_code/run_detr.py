from transformers import DetrImageProcessor, DetrForObjectDetection
import torch
from PIL import Image
import requests
import matplotlib.pyplot as plt 

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

url = "http://images.cocodataset.org/val2017/000000039769.jpg"
#image = Image.open(requests.get(url, stream=True).raw)
image = Image.open('detr_test_code/LeFish.png')
if image.mode != 'RGB':
    image = image.convert('RGB')

# you can specify the revision tag if you don't want the timm dependency
processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-101", revision="no_timm")
# model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-101", revision="no_timm")
model = torch.load('detr_test_code/DETR.pt', weights_only=False)

inputs = processor(images=image, return_tensors="pt")
# inputs.to(device)
outputs = model(**inputs)

# convert outputs (bounding boxes and class logits) to COCO API
# let's only keep detections with score > 0.9
target_sizes = torch.tensor([image.size[::-1]])
results = processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=0.9)[0]

for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
    box = [round(i, 2) for i in box.tolist()]
    print(
            f"Detected {model.config.id2label[label.item()]} with confidence "
            f"{round(score.item(), 3)} at location {box}"
    )

def reveal_image_and_bbox(image, bboxes, labels, scores, id2label):
    # Create a plot
    plt.figure(figsize=(10, 10))
    plt.imshow(image)
    ax = plt.gca()

    # Draw each bounding box with label and score
    for bbox, label, score in zip(bboxes, labels, scores):
        bbox = bbox.detach().numpy() 
        x_min, y_min, x_max, y_max = bbox
        
        # Create a rectangle patch
        rect = plt.Rectangle((x_min, y_min), x_max - x_min, y_max - y_min, 
                             linewidth=2, edgecolor='r', facecolor='none')
        ax.add_patch(rect)
        
        # Add label and score
        ax.text(x_min, y_min, f"{id2label[label.item()]}: {round(score.item(), 3)}", 
                fontsize=12, color='blue', bbox=dict(facecolor='red', alpha=0.5))

    plt.axis('off')
    plt.show()

reveal_image_and_bbox(image, results["boxes"], results["labels"], results["scores"], model.config.id2label)