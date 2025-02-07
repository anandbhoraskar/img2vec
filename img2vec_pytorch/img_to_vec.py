import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
import torchvision.transforms as transforms
import numpy as np

class Img2Vec():

    def __init__(self, cuda=False, model='resnet-50', layer='default',
                 layer_output_size=2048, channels=1, return_embedding=False,
                 centre_crop=False):
        """ Img2Vec
        :param cuda: If set to True, will run forward pass on GPU
        :param model: String name of requested model
        :param layer: String or Int depending on model.  See more docs: https://github.com/christiansafka/img2vec.git
        :param layer_output_size: Int depicting the output size of the requested layer
        """
        self.device = torch.device("cuda" if cuda else "cpu")
        self.layer_output_size = layer_output_size
        self.model_name = model
        
        self.model, self.extraction_layer = self._get_model_and_layer(model, layer)

        self.model = self.model.to(self.device)

        self.model.eval()

        if centre_crop:
            self.scaler = transforms.CenterCrop((224, 224))
        else:
            self.scaler = transforms.Resize((224, 224))
        self.normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                              std=[0.229, 0.224, 0.225])
        self.to_tensor = transforms.ToTensor()
        self.channels = channels
        self.return_embedding = return_embedding

    def get_vec(self, img, tensor=False):
        """ Get vector embedding from PIL image
        :param img: PIL Image or list of PIL Images
        :param tensor: If True, get_vec will return a FloatTensor instead of Numpy array
        :returns: Numpy ndarray
        """

        image = self.normalize(self.to_tensor(self.scaler(img))).unsqueeze(0).to(self.device)

        def copy_data(m, i, o):

            global my_embedding
            my_embedding = o.data.clone()

        h = self.extraction_layer.register_forward_hook(copy_data)
        h_x = self.model(image)
        h.remove()

        if self.return_embedding:
            return my_embedding

        my_embedding = F.adaptive_avg_pool2d(my_embedding, (1, 1))

        if tensor:
            return my_embedding
        else:
            return my_embedding.numpy()[0, :, 0, 0]

    def _get_model_and_layer(self, model_name, layer):
        """ Internal method for getting layer from model
        :param model_name: model name such as 'resnet-18'
        :param layer: layer as a string for resnet-18 or int for alexnet
        :returns: pytorch model, selected layer
        """
        if model_name == 'resnet-18':
            model = models.resnet18(pretrained=True)
            if layer == 'default':
                layer = model._modules.get('avgpool')
            else:
                layer = model._modules.get(layer)

            return model, layer
        
        if model_name == 'resnet-50':
            model = models.resnet50(pretrained=True)
            if layer == 'default':
                layer = model._modules.get('avgpool')
            else:
                layer = model._modules.get(layer)

            return model, layer

        else:
            raise KeyError('Model %s was not found' % model_name)
