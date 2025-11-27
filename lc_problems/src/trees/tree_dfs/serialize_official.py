from binary_tree import *
from tree_node import *

# Initializing our marker
MARKER = "M"
m = 1

def serialize_rec(node, stream):
    global m

    if node is None:
        stream.append(MARKER + str(m))
        m += 1
        return

    stream.append(node.data)

    serialize_rec(node.left, stream)
    serialize_rec(node.right, stream)

# Function to serialize tree into list of integers.
def serialize(root):
    stream = []
    serialize_rec(root, stream)
    return stream

def deserialize_helper(stream):
    val = stream.pop()

    if type(val) is str and val[0] == MARKER:
        return None

    node = TreeNode(val)

    node.left = deserialize_helper(stream)
    node.right = deserialize_helper(stream)

    return node

# Function to deserialize integer list into a binary tree.
def deserialize(stream):
    stream.reverse()
    node = deserialize_helper(stream)
    return node

# Driver code
def main():
    global m
    input_trees = [
        [TreeNode(100), TreeNode(50), TreeNode(200), TreeNode(25), TreeNode(75), TreeNode(350)],
        [TreeNode(100), TreeNode(200), TreeNode(75), TreeNode(50), TreeNode(25), TreeNode(350)],
        [TreeNode(200), TreeNode(350), TreeNode(100), TreeNode(75), TreeNode(50), TreeNode(200), TreeNode(25)],
        [TreeNode(25), TreeNode(50), TreeNode(75), TreeNode(100), TreeNode(200), TreeNode(350)],
        [TreeNode(350), TreeNode(75), TreeNode(25), TreeNode(200), TreeNode(50), TreeNode(100)],
        [TreeNode(1), None, TreeNode(2), None, TreeNode(3), None, TreeNode(4), None, TreeNode(5)]
    ]

    indx = 1
    for i in input_trees:
        tree = BinaryTree(i)

        print(indx, ".\tBinary Tree:", sep="")
        indx += 1
        if tree.root is None:
            display_tree(None)
        else:
            display_tree(tree.root)

        print("\n\tMarker used for NULL nodes in serialization/deserialization: ",
              MARKER, "*", sep="")

        # Serialization
        ostream = serialize(tree.root)
        print("\n\tSerialized integer list:")
        print("\t" + str(ostream))

        # Deserialization
        deserialized_root = deserialize(ostream)
        print("\n\tDeserialized binary tree:")
        display_tree(deserialized_root)
        print("-"*100)
        m = 1

if __name__ == '__main__':
    main()