import os
import numpy as np
import cv2
import dlib
import torch
from torchvision import transforms
import torch.nn.functional as F
from model.vtoonify import VToonify
from model.bisenet.model import BiSeNet
from model.encoder.align_all_parallel import align_face
from util import save_image, load_image, visualize, load_psp_standalone, get_video_crop_parameter, tensor2cv2

# Set device to CPU
device = "cpu"

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
])

vtoonify_models = {
    'cartoon4-d': './checkpoint/vtoonify_s_d.pt',
    'cartoon3-d': './checkpoint/vtoonify_s_d.pt',
    'cartoon5-d': './checkpoint/vtoonify_s_d.pt'
}

parsing_model_path = './checkpoint/faceparsing.pth'
style_encoder_path = './checkpoint/encoder.pt'
landmark_predictor_path = './checkpoint/shape_predictor_68_face_landmarks.dat'

# Load models once to reuse
vtoonify_instances = {name: VToonify(backbone='dualstylegan').to(device) for name in vtoonify_models}
for name, model in vtoonify_instances.items():
    model.load_state_dict(torch.load(vtoonify_models[name], map_location=device)['g_ema'])

parsing_predictor = BiSeNet(n_classes=19)
parsing_predictor.load_state_dict(torch.load(parsing_model_path, map_location=device))
parsing_predictor.to(device).eval()

if not os.path.exists(landmark_predictor_path):
    import wget, bz2
    wget.download('http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2', landmark_predictor_path + '.bz2')
    with bz2.BZ2File(landmark_predictor_path + '.bz2') as zipfile:
        data = zipfile.read()
        with open(landmark_predictor_path, 'wb') as f:
            f.write(data)

landmark_predictor = dlib.shape_predictor(landmark_predictor_path)
psp_encoder = load_psp_standalone(style_encoder_path, device)

exstyle_path = './checkpoint/exstyle_code.npy'
exstyles = np.load(exstyle_path, allow_pickle='TRUE').item()

def process_image_with_vtoonify(input_path, output_path, model_key, style_degree, style_id):
    vtoonify = vtoonify_instances[model_key]
    exstyle = torch.tensor(exstyles[list(exstyles.keys())[style_id]]).to(device)
    with torch.no_grad():
        exstyle = vtoonify.zplus2wplus(exstyle)

    image = cv2.imread(input_path)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    I = align_face(image, landmark_predictor)
    I = transform(I).unsqueeze(dim=0).to(device)

    s_w = psp_encoder(I)
    s_w = vtoonify.zplus2wplus(s_w)
    s_w[:, :7] = exstyle[:, :7]

    x = transform(image).unsqueeze(dim=0).to(device)
    x_p = F.interpolate(parsing_predictor(2 * F.interpolate(x, scale_factor=2, mode='bilinear', align_corners=False))[0],
                        scale_factor=0.5, recompute_scale_factor=False).detach()
    inputs = torch.cat((x, x_p / 16.), dim=1)
    y_tilde = vtoonify(inputs, s_w.repeat(inputs.size(0), 1, 1), d_s=style_degree)
    y_tilde = torch.clamp(y_tilde, -1, 1)

    save_image(y_tilde[0].cpu(), output_path)
    return output_path
