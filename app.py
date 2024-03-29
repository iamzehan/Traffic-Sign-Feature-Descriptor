from datetime import date
import tensorflow as tf
import pandas as pd
import gradio as gr
import numpy as np
import cv2 as cv2

def shapeModel():
  labels=["Octagon","Triangle","Circle Prohibitory","Circle","Rhombus"]
  json_file = open('./model/model1.json', 'r')
  loaded_model_json = json_file.read()
  json_file.close()
  model = tf.keras.models.model_from_json(loaded_model_json)
  model.load_weights("./model/model1.h5")
  return [model,labels]

def recognitionModel():
  json_file = open('./recognition_model/model.json', 'r')
  loaded_model_json = json_file.read()
  json_file.close()
  model = tf.keras.models.model_from_json(loaded_model_json)
  model.load_weights("./recognition_model/model.h5")
  return model


def dark_image(h,w):
    image = np.zeros((h, w, 3), np.uint8) * 255
    return image

#------------------------ ⬇⬇⬇ Extracting Shape Regions ⬇⬇⬇ -----------------------------
def fill(img):
  h,w=img.shape
  image=dark_image(h,w)
  cnts = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
  cnts = cnts[0] if len(cnts) == 2 else cnts[1]
  for c in cnts:
      cv2.drawContours(image,[c], 0, (255,255,255), -1)
  return image

#------------------------- ➡➡➡ This block ends ⬅⬅⬅ --------------------------------

#------------------------ ⬇⬇⬇ Segmenting Red Regions ⬇⬇⬇ -----------------------------
def red_mask(image):
    lower_red_1 = np.array([0, 100, 20])
    upper_red_1 = np.array([10, 255, 255])

    lower_red_2 = np.array([160,100,20])
    upper_red_2 = np.array([179,255,255]) 
    
    lower_red_mask = cv2.inRange(image, lower_red_1, upper_red_1)
    upper_red_mask = cv2.inRange(image, lower_red_2, upper_red_2)

    red_full_mask = lower_red_mask + upper_red_mask

    return red_full_mask

def red_fill(img):
  h,w=img.shape
  image=dark_image(h,w)
  cnts = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
  cnts = cnts[0] if len(cnts) == 2 else cnts[1]
  for c in cnts:
      cv2.drawContours(image,[c], 0, (255,0,0), -1)
  return image
#------------------------- ➡➡➡ This block ends ⬅⬅⬅ -----------------------------------


#-------------------------- ⬇⬇⬇ Segmenting Blue Regions ⬇⬇⬇---------------------------

def blue_mask(image):
    lower_blue_1 = np.array([112,50,50])
    upper_blue_1 = np.array([130,255,255])

    lower_blue_2 = np.array([96, 80, 2])
    upper_blue_2 = np.array([126, 255, 255])

    lower_blue_mask =cv2.inRange(image, lower_blue_1, upper_blue_1)
    upper_blue_mask =cv2.inRange(image, lower_blue_2, upper_blue_2)

    blue_full_mask = lower_blue_mask + upper_blue_mask 

    return blue_full_mask

def blue_fill(img):
  h,w=img.shape
  image=dark_image(h,w)
  cnts = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
  cnts = cnts[0] if len(cnts) == 2 else cnts[1]
  for c in cnts:
      cv2.drawContours(image,[c], 0, (0,0,255), -1)
  return image

#------------------------- ➡➡➡ This block ends ⬅⬅⬅ -----------------------------------

#-------------------------- ⬇⬇⬇ Calculating Center of Image ⬇⬇⬇---------------------------
def coi(img):
  gray_img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
  moment = cv2.moments(gray_img)
  X = int(moment ["m10"] / moment["m00"])
  Y = int(moment ["m01"] / moment["m00"])
  return X+10,Y+8
#------------------------- ➡➡➡ This block ends ⬅⬅⬅ -----------------------------------

def resize(img):
    # img= cv2.bilateralFilter(img,9,75,75)
    width = 32
    height = 32
    dim = (width, height)
    resized=cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
    return resized


def shape_recognition(number, image):
    model=shapeModel()[0]
    labels=shapeModel()[1]
    image=resize(image)
    image_array= np.expand_dims(image, axis=0)
    predictions=model.predict(image_array)
    score = tf.nn.softmax(predictions[0])
    # return {f"{number +' '+ labels[i] }": float(score[i]) for i in range(len(labels))}
    return f'Shape {str(number)}:'+" "+ f'{labels[np.argmax(score)]}'

def ts_recognition(number, image):
    model=recognitionModel()
    labels=pd.read_csv('./recognition_model/labels.csv')
    labels=labels['Name']
    image=resize(image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    image_array= np.expand_dims(image, axis=0)
    predictions=model(image_array)
    score = tf.nn.softmax(predictions[0])
    # return {f"{number +' '+ labels[i] }": float(score[i]) for i in range(len(labels))}
    return f'Sign {str(number)}:'+" "+ f'{labels[np.argmax(score)]}'

def outputs(roi):
    shape_n=[]
    color=[]
    sign=[]
    count=1
    for i in roi:
      result = i.copy()
      x,y=list(coi(i))
      image = cv2.cvtColor(result, cv2.COLOR_RGB2HSV)
      
      red_full_mask = red_mask(image)

      blue_full_mask = blue_mask(image)

      filled_red=red_fill(red_full_mask)
      filled_blue=blue_fill(blue_full_mask)

    #   x=center_of_image[0]
    #   y=center_of_image[1]

      rb_img=filled_red+filled_blue


      
      if list(rb_img[y,x])==[255,0, 0] or list(rb_img[y,x])==[255,0, 255]:
        # save(fill(red_full_mask))
        #print(fill(red_full_mask).shape)
        shape_n.append(shape_recognition(count,fill(red_full_mask)))
        color.append(f"Color {count}: Red")
        sign.append(ts_recognition(count,result))
      elif list(rb_img[y,x])==[0, 0, 255]:
        # print(fill(red_full_mask).shape)
        shape_n.append(shape_recognition(count,fill(blue_full_mask)))
        color.append(f"Color {count}: Blue")
        sign.append(ts_recognition(count,result))

      else:
        shape_n.append(f"Shape {count}: Undefined")
        color.append(f"Color {count}: Undefined")
        sign.append(ts_recognition(count,result))
      count+=1
    return shape_n, color ,sign

def detect(image):
    with tf.io.gfile.GFile('./detection_model/frozen_inference_graph.pb', 'rb') as f:
        graph_def = tf.compat.v1.GraphDef()
        graph_def.ParseFromString(f.read())

    with tf.compat.v1.Session() as sess:
        # Restore session
        sess.graph.as_default()
        tf.import_graph_def(graph_def, name='')

        # Read and preprocess an image.
        img = image
        cropper=img.copy()
        rows = img.shape[0]
        cols = img.shape[1]
        inp = cv2.resize(img, (300, 300))
        #inp = inp[:, :, [2, 1, 0]]  # BGR2RGB

        # Run the model
        out = sess.run([sess.graph.get_tensor_by_name('num_detections:0'),
                        sess.graph.get_tensor_by_name('detection_scores:0'),
                        sess.graph.get_tensor_by_name('detection_boxes:0'),
                        sess.graph.get_tensor_by_name('detection_classes:0')],
                    feed_dict={'image_tensor:0': inp.reshape(1, inp.shape[0], inp.shape[1], 3)})     
        # Visualize detected bounding boxes.
        num_detections = int(out[0][0])
        roi=[]
        for i in range(num_detections):
            classId = int(out[3][0][i])
            score = float(out[1][0][i])
            bbox = [float(v) for v in out[2][0][i]]
            if score > 0.8:
                x = (bbox[1] * cols) -10 #left
                y = (bbox[0] * rows) - 15 #top
                right = (bbox[3] * cols) + 10
                bottom = (bbox[2] * rows ) +10
                crop=cropper[int(y): int(bottom),int(x):int(right)]
                if crop.shape[0]!=0 and crop.shape[1]!=0:
                  roi.append(crop)
                  detect=cv2.rectangle(img, (int(x), int(y)), (int(right), int(bottom)), (15, 255,100), thickness=4)
                  cv2.putText(detect, f'{i+1}', (int(x), int(y-10)), cv2.FONT_HERSHEY_PLAIN, 0.8, (255,255,0), 2) 
    if roi:
      shape_n,color, sign=outputs(roi)
      return detect, ', '.join(shape_n), ', '.join(color), ', '.join(sign)
    else:
      return image, 'Undetected', 'Undetected', 'Undetected'

iface=gr.Interface(detect,
    inputs=gr.inputs.Image(label="Upload an Image"),
    outputs=[gr.outputs.Image(label="Detected Image"),
    gr.outputs.Label(label="Shape"),
    # gr.outputs.Image(label="Removed Background Image"),
    gr.outputs.Label(label="Color"),
    gr.outputs.Label(label="Signs")
    ],
    title="Bangladeshi Traffic Sign, Detection, Shape-Color Recognition & Classification",
    examples=['examples/1.jpg','./examples/2.jpg', './examples/4.jpg'],
    layout='center',
    description='The following is an Implementation of a Thesis paper done by Md. Ziaul Karim, \n for the Department of Software Engineering, Daffodil International University\'s Undergraduate program as a proof of concept.',
    theme='dark-peach',css='./style.css',article=f'<a href="https://codingwithzk.netlify.app", target="_blank">© {date.today().year} Copyright | Made by <strong>Ziaul Karim</strong></a><a href="https://gradio.app/"> | with <strong>Gradio</strong></a>'
)

iface.launch(debug=True, favicon_path='./favicon.png',height=300,width=500)
