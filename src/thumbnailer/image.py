from logging import debug, info
from PIL import Image


def reorient_image(im):
    try:
        image_exif = im._getexif()
        image_orientation = image_exif[274]
        if image_orientation in (2, '2'):
            return im.transpose(Image.FLIP_LEFT_RIGHT)
        elif image_orientation in (3, '3'):
            return im.transpose(Image.ROTATE_180)
        elif image_orientation in (4, '4'):
            return im.transpose(Image.FLIP_TOP_BOTTOM)
        elif image_orientation in (5, '5'):
            return im.transpose(Image.ROTATE_90).transpose(Image.FLIP_TOP_BOTTOM)
        elif image_orientation in (6, '6'):
            return im.transpose(Image.ROTATE_270)
        elif image_orientation in (7, '7'):
            return im.transpose(Image.ROTATE_270).transpose(Image.FLIP_TOP_BOTTOM)
        elif image_orientation in (8, '8'):
            return im.transpose(Image.ROTATE_90)
        else:
            return im
    except (KeyError, AttributeError, TypeError, IndexError):
        return im


def crop_max_square(pil_img, dims, resample=Image.LANCZOS):
    """
  Crops the largest sized square from the center area of the image, then resizes to the given dimensions.
  """
    img = crop_center(pil_img, min(pil_img.size), min(pil_img.size))
    return img.resize(dims, resample=resample)


def crop_center(pil_img, crop_width, crop_height):
    """
  crops the central area of the image
  """
    img_width, img_height = pil_img.size
    return pil_img.crop(
        (
            (img_width - crop_width) // 2,
            (img_height - crop_height) // 2,
            (img_width + crop_width) // 2,
            (img_height + crop_height) // 2,
        )
    )


def resize(filename, width, height):
    info(f'resizing {filename} to {width}x{height}')
    dims = width, height
    debug(f'creating thumbnail with dimensions: {dims}')
    im = Image.open(filename)
    im_o = reorient_image(im)
    nim = crop_max_square(im_o, dims)
    nim.save(filename)
