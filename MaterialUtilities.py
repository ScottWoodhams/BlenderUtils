import bpy
from Utilities.Enums.DCCs import BlenderMaterialTextureSlots


class MaterialUtilities(object):

    @staticmethod
    def getTextures(objects):
        """
            Return paths for all textures inside an objects active material
        :param objects:
        """
        images = []

        for mesh in [o for o in objects if o.type == "MESH"]:
            for textureNode in [node for node in mesh.active_material.node_tree.nodes if node.type == "TEX_IMAGE"]:
                images.append(textureNode.image.filepath)

        return images

    @staticmethod
    def getTextureFromSlot(material, slot: BlenderMaterialTextureSlots):
        """
        Method to get the node connected to a Prinicpled BSDF material node input slot
        :param material: material to search for texture node on
        :param slot: material input slot to search material for texture from
        :return: return the connected node to the provided texture slot, None if no node is linked
        To get the texture file path from the returned node, use node.image.filepath
        """
        # Get the Principled BSDF node
        shaderGraph = material.node_tree.nodes.get("Principled BSDF", None)

        # Get the node linked to the provided input slot
        if shaderGraph.inputs[slot.value].links:
            # If search for the normal map slot
            if slot == BlenderMaterialTextureSlots.Normal:
                # Get the texture node linked to the Normal Map space transform node
                return shaderGraph.inputs[slot.value].links[0].from_node.inputs["Color"].links[0].from_node

            # Return the texture node connected to ht provided input slot
            return shaderGraph.inputs[slot.value].links[0].from_node

        # No texture node linked to the provided input slot
        return None

    @staticmethod
    def setTextureBySlot(material, slot: BlenderMaterialTextureSlots, texture_node=None, texture_path=None):
        """
        Method to connect a texture node to a specified material input slot
        :param material: material to assign the texture to the assigned slot
        :param texture_node: node of the texture image to assign
        :param slot: material input slot to link
        :return: bool if assignment is successful or failed
        """

        # If no texture node was provided, get an existing texture link and assign the new image
        if not texture_node:
            texture_node = MaterialUtilities.getTextureFromSlot(material, slot)
            if texture_node:
                # Load the image
                img = bpy.data.images.load(texture_path, check_existing=True)
                # Assign the image
                texture_node.image = img
                return True

        # Get the Principled BSDF node
        shaderGraph = material.node_tree.nodes.get("Principled BSDF", None)
        inputNode = shaderGraph.inputs[slot.value]

        # If no texture node was provided and no existing link was found, create a new link
        if not texture_node:
            texture_node = MaterialUtilities.createTextureNode(material.node_tree, texture_path)

        # Connect the texture to the material input slot
        material.node_tree.links.new(texture_node.outputs[0], inputNode)

        return True

    @staticmethod
    def createTextureNode(node_tree, texture_path):
        """
        Method to create a texture node in the provided material node tree
        :param node_tree: material node tree where the texture node will be created
        :param texture_path: str file path of the texture
        :return: texture node
        """
        # Create the texture node
        texNode = node_tree.nodes.new(type="ShaderNodeTexImage")

        # Load the texture image
        img = bpy.data.images.load(texture_path, check_existing=True)

        # Assign the image to the texture node
        texNode.image = img

        return texNode
