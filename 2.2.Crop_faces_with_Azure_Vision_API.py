import http.client
import json
import os.path
import urllib.error
import urllib.parse

import cv2
from dotenv import load_dotenv

load_dotenv()

base_path = '.\\Training Sample Videos\\'
AZURE_COMPUTER_VISION_NAME = os.getenv('AZURE_COMPUTER_VISION_NAME')  # Azure endpoint URL.
AZURE_COMPUTER_VISION_API_KEY = os.getenv('AZURE_COMPUTER_VISION_API_KEY')  # Input API key from Azure account.


def get_file_name(file_path):
    filename_basename = os.path.basename(file_path)
    filename_only = filename_basename.split('.')[0]
    return filename_only


with open(os.path.join(base_path, 'metadata.json')) as metadata_json:
    metadata = json.load(metadata_json)
    print(len(metadata))

for filename in metadata.keys():
    tmp_path = os.path.join(base_path, get_file_name(filename))
    print('Processing Directory...! ' + tmp_path)
    frame_images = [x for x in os.listdir(tmp_path) if os.path.isfile(os.path.join(tmp_path, x))]
    faces_path = os.path.join(tmp_path, 'faces')
    print('Creating Directory...!')
    os.makedirs(faces_path, exist_ok=True)
    print('Cropping faces from the images...!')

    for frame in frame_images:
        print('Processing... ', frame)
        image = cv2.cvtColor(cv2.imread(os.path.join(tmp_path, frame)), cv2.COLOR_BGR2RGB)

        # Open binary file
        with open(os.path.join(tmp_path, frame), 'rb') as file_contents:
            img_data = file_contents.read()

        # Azure Computer Vision API
        headers = {
            # Request header
            'Content-Type': 'application/octet-stream',
            'Ocp-Apim-Subscription-Key': AZURE_COMPUTER_VISION_API_KEY,
        }

        params = urllib.parse.urlencode({
            # Request parameters
            'visualFeatures': 'Faces'
        })

        try:
            conn = http.client.HTTPSConnection(AZURE_COMPUTER_VISION_NAME)
            conn.request('POST', '/vision/v3.0/analyze?%s' % params, img_data, headers)
            response = conn.getresponse().read()
            data = json.loads(response.decode('utf-8'))
            print(data)
            conn.close()
        except IOError as e:
            print('[Errno {0}] {1}'.format(e.errno, e.strerror))
            continue

        print(data['faces'])
        print('Face Detected...: ', len(data['faces']))
        count = 0

        for result in data['faces']:
            bounding_box = [result['faceRectangle']['left'], result['faceRectangle']['top'],
                            result['faceRectangle']['width'], result['faceRectangle']['height']]
            print(bounding_box)

            margin_x = bounding_box[2] * 0.3  # Occupies 30% as the margin
            margin_y = bounding_box[3] * 0.3  # Occupies 30% as the margin
            x1 = int(bounding_box[0] - margin_x)
            if x1 < 0:
                x1 = 0
            x2 = int(bounding_box[0] + bounding_box[2] + margin_x)
            if x2 > image.shape[1]:
                x2 = image.shape[1]
            y1 = int(bounding_box[1] - margin_y)
            if y1 < 0:
                y1 = 0
            y2 = int(bounding_box[1] + bounding_box[3] + margin_y)
            if y2 > image.shape[0]:
                y2 = image.shape[0]
            print(x1, y1, x2, y2)
            crop_image = image[y1:y2, x1:x2]
            new_filename = '{}-{:02d}.png'.format(os.path.join(faces_path, get_file_name(frame)), count)
            count = count + 1
            cv2.imwrite(new_filename, cv2.cvtColor(crop_image, cv2.COLOR_RGB2BGR))
