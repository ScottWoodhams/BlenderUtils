import bpy
import os
from Utilities.FileObjects.FilePath import FilePath
from Utilities.Blender.SceneUtilities import SceneUtilities


class CompositorUtilities(object):
    """
    A collection of utilities for creating, manipulating and rendering images from Blender Compositing
    https://docs.blender.org/manual/en/latest/compositing/index.html
    https://docs.blender.org/api/current/bpy.types.CompositorNode.html
    """

    @staticmethod
    def initCompositor(output_node_type="CompositorNodeOutputFile"):
        """
        Method to initalise the Blender Compositor node tree with a default file output node
        :param output_node_type: str of the output node to create eg. CompositorNodeOutputFile for image file output
        :return: tuple of the compositor node tree and the output node object
        """
        # Switch on nodes and get scene reference
        bpy.context.scene.use_nodes = True
        nodeTree = bpy.context.scene.node_tree
        outputNode = nodeTree.nodes.new(type=output_node_type)

        return nodeTree, outputNode

    @staticmethod
    def renderComposition(node_tree, do_cleanup=True, frame=0):
        """
        Method to render the current node tree composition to the output node
        :param node_tree: Compositor node tree to render
        :param do_cleanup: bool do clear out the node tree after rendering
        :param frame: int frame to render - will append frame number with four digit padding to output file eg. '0000'
        :return:
        """
        # Ensure a camera exists prior to rendering
        if not bpy.context.scene.camera:
            # TODO: check but this should NOT be used in billboard
            print("COMPOSITOR UTILS: creating RenderCam in active collection")
            SceneUtilities.createCamera(name="RenderCam")

        # Ensure the frame render frame is at the first index to force the Blender suffix to be a known value of '0000'
        bpy.context.scene.frame_set(frame)

        # Render the tmp roughness image
        bpy.ops.render.render(write_still=True)

        # Clean node tree
        if do_cleanup:
            for node in node_tree.nodes:
                node_tree.nodes.remove(node)

    @staticmethod
    def removeBlenderFrameSuffix(file_path, frame=0):
        """
        Method to rename the output file stripping off the automatic Blender render frame suffix eg. '0000'
        :param file_path: FilePath object of the provided output file to the render output node (does not include '0000' suffix)
        :param frame: int the frame the image was rendered for
        :return:
        """
        # Cleanup roughness files to one TMP file without the blender ID suffix
        if file_path.exists():
            # If the final destination name exists, remove it
            file_path.removeFile()

        # Remove Blender standard '0000' suffix
        tmpOutput = file_path.getFullPath(path_only=True) + "/" + file_path.fileName + "0000" + "." + file_path.fileExt
        os.rename(tmpOutput, file_path.getFullPath())

    @staticmethod
    def extractAlphaToGreyscale(src_img, dst_img=None, dst_suffix=None, format='TARGA', do_cleanup=True):
        """
        Method to render and save to the alpha channel of the provided source image as its own greyscale image
        :param src_img: str file path of the source image
        :param dst_img: str file path of the destination image - replaces entire file path of source image
        :param dst_suffix: str replacement suffix of the destination image -
        keeps entire file path of source image, only replacing the suffix
        :param format: str file format of the output image in Blender formatted string eg. TARGA, PNG, JPEG, TIFF
        :param do_cleanup: bool clear the compositing node tree of all nodes after rendering
        :return:
        """
        # Switch on nodes and get scene reference
        nodeTree, outputNode = CompositorUtilities.initCompositor()

        # Create input node
        inputNode = nodeTree.nodes.new(type="CompositorNodeImage")

        # Connect nodes -
        # link the alpha pin (1) on the input node to the color pin (0) on the output node
        nodeTree.links.new(inputNode.outputs[1], outputNode.inputs[0])

        # Assign input image
        srcTex = FilePath(src_img)
        img = bpy.data.images.load(srcTex.getFullPath(), check_existing=True)
        inputNode.image = img

        # Use the provided full destination file path if available
        if dst_img:
            dstTex = FilePath(dst_img)
        # Otherwise replace the source texture's suffix with a provided suffix
        elif dst_suffix:
            dstTex = FilePath(srcTex.getFullPath(path_only=True), has_name=False)
            dstTex.fileName = '_'.join([srcTex.fileName, dst_suffix])
            dstTex.fileExt = srcTex.fileExt
        # If no path or suffix is provided, use the source as destination
        else:
            dstTex = FilePath(srcTex.getFullPath())

        # Assign output image path
        outputNode.base_path = dstTex.getFullPath(path_only=True)

        # Assign output image name
        for filePath in outputNode.file_slots:
            filePath.path = dstTex.fileName

        # Assign output file type (extension)
        outputNode.format.file_format = format

        # Assign the output color mode
        outputNode.format.color_mode = 'BW'

        # Render out greyscale texture
        CompositorUtilities.renderComposition(nodeTree, do_cleanup=do_cleanup)

        # Remove Blender standard '0000' suffix
        CompositorUtilities.removeBlenderFrameSuffix(dstTex)

        return dstTex

    @staticmethod
    def packGreyscaleToAlpha(src_rgb, src_greyscale, expected_src_suffix="_A", dst_suffix="_AR", format='TARGA', do_cleanup=True):
        """
        Method to pack a greyscale texture into the alpha channel of an RGBA texture
        :param src_rgb: str file path of the texture to use as the RGB channels of the output image
        :param src_greyscale: str file path of the greyscale texture to pack into the Alpha channel of the output image
        :param format: str file format of the output image in Blender formatted string eg. TARGA, PNG, JPEG, TIFF
        :param do_cleanup: bool do clear the compositor node tree after rendering
        :return:
        """
        # Switch on nodes and get scene reference
        nodeTree, outputNode = CompositorUtilities.initCompositor()

        # Create input nodes
        inputRgbNode = nodeTree.nodes.new(type="CompositorNodeImage")
        inputAlphaNode = nodeTree.nodes.new(type="CompositorNodeImage")

        # Separate RGB from input image
        splitNode = nodeTree.nodes.new(type="CompositorNodeSeparateXYZ")

        # Create merge node
        mergeNode = nodeTree.nodes.new(type="CompositorNodeCombineColor")

        # Assign input RGB image
        srcRgbTex = FilePath(src_rgb)
        img = bpy.data.images.load(srcRgbTex.getFullPath(), check_existing=True)
        inputRgbNode.image = img

        # Assign input Greyscale image
        srcAlphaTex = FilePath(src_greyscale)
        img = bpy.data.images.load(srcAlphaTex.getFullPath(), check_existing=True)
        inputAlphaNode.image = img
        inputAlphaNode.image.colorspace_settings.name = "Non-Color"

        # Connect nodes -
        # link the image pin (0) on the input RGB node to the input pin (0) on the channel split node
        nodeTree.links.new(inputRgbNode.outputs[0], splitNode.inputs[0])

        # link the channel split pins (0-2) from the input RGB node to the input pins (0-2) on the channel merge node
        # connecting RGB from source to output
        nodeTree.links.new(splitNode.outputs[0], mergeNode.inputs[0])
        nodeTree.links.new(splitNode.outputs[1], mergeNode.inputs[1])
        nodeTree.links.new(splitNode.outputs[2], mergeNode.inputs[2])
        # link the image pin (0) on the input Greyscale node to the alpha input pin (3) on the channel merge node
        nodeTree.links.new(inputAlphaNode.outputs[0], mergeNode.inputs[3])

        # link the RGBA color pin (0) on the channel merge node to the image input pin (0) on the image output node
        nodeTree.links.new(mergeNode.outputs[0], outputNode.inputs[0])

        # Assign output image path
        outputNode.base_path = srcRgbTex.getFullPath(path_only=True)

        # Assign output image name
        srcRgbTex.fileName = srcRgbTex.fileName.replace(expected_src_suffix, dst_suffix)
        for filePath in outputNode.file_slots:
            filePath.path = srcRgbTex.fileName

        # Assign output file type (extension)
        outputNode.format.file_format = format

        # Assign the output color mode
        outputNode.format.color_mode = 'RGBA'

        # Render texture
        CompositorUtilities.renderComposition(nodeTree, do_cleanup=do_cleanup)

        # Remove Blender frame suffix eg. '0000'
        CompositorUtilities.removeBlenderFrameSuffix(srcRgbTex)

    @staticmethod
    def blendImages(src_image_01, src_image_02, mix_type="MULTIPLY", image_01_type="sRGB", image_02_type="sRGB", format="TARGA", do_cleanup=True):
        """
        Method to blend two images with a default Multiply blend type
        :param src_image_01: str of file path of first image for blend
        :param src_image_02: str of file path of second image for blend
        :param mix_type: str of the image mixing blend type in Blender formatted string eg. MULTIPLY, DARKEN, COLOR BURN etc.
        :param format: str file format of the output image in Blender formatted string eg. TARGA, PNG, JPEG, TIFF
        :param do_cleanup: bool do clear the compositor node tree after rendering
        :return:
        """
        # Switch on nodes and get scene reference
        nodeTree, outputNode = CompositorUtilities.initCompositor()

        # Create input nodes
        inputImage01Node = nodeTree.nodes.new(type="CompositorNodeImage")
        inputImage02Node = nodeTree.nodes.new(type="CompositorNodeImage")

        # Create the multiply node
        mixNode = nodeTree.nodes.new(type="CompositorNodeMixRGB")

        # Assign input RGB image
        srcImageTex = FilePath(src_image_01)
        img = bpy.data.images.load(srcImageTex.getFullPath(), check_existing=True)
        inputImage01Node.image = img
        inputImage01Node.image.colorspace_settings.name = image_01_type

        # Assign input Greyscale image
        secondaryImageTex = FilePath(src_image_02)
        img = bpy.data.images.load(secondaryImageTex.getFullPath(), check_existing=True)
        inputImage02Node.image = img
        inputImage02Node.image.colorspace_settings.name = image_02_type

        # Connect nodes -
        # link the image pin (0) on the input RGB node to the input pin (0) on the channel split node
        nodeTree.links.new(inputImage01Node.outputs[0], mixNode.inputs[1])
        nodeTree.links.new(inputImage02Node.outputs[0], mixNode.inputs[2])

        # Link the RGB mix node to the output file node
        nodeTree.links.new(mixNode.outputs[0], outputNode.inputs[0])

        # Set the RGB mix blend type
        mixNode.blend_type = mix_type

        # Assign output image path
        outputNode.base_path = srcImageTex.getFullPath(path_only=True)

        # Assign output image name
        for filePath in outputNode.file_slots:
            filePath.path = srcImageTex.fileName

        # Assign output file type (extension)
        outputNode.format.file_format = format

        # Assign the output color mode
        outputNode.format.color_mode = 'RGBA'

        # Render texture
        CompositorUtilities.renderComposition(nodeTree, do_cleanup=do_cleanup)

        # Remove Blender frame suffix eg. '0000'
        CompositorUtilities.removeBlenderFrameSuffix(srcImageTex)
