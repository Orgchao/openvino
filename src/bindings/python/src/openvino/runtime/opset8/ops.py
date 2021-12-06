# Copyright (C) 2018-2021 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Factory functions for all openvino ops."""
from functools import partial
from typing import Callable, Iterable, List, Optional, Set, Union, Tuple

import numpy as np
from openvino.runtime.exceptions import UserInputError
from openvino.runtime.impl import Node, Shape
from openvino.runtime.impl.op import Constant, Parameter
from openvino.runtime.opset_utils import _get_node_factory
from openvino.runtime.utils.decorators import binary_op, nameable_op, unary_op
from openvino.runtime.utils.input_validation import (
    assert_list_of_ints,
    check_valid_attributes,
    is_non_negative_value,
    is_positive_value,
)
from openvino.runtime.utils.node_factory import NodeFactory
from openvino.runtime.utils.tensor_iterator_types import (
    GraphBody,
    TensorIteratorSliceInputDesc,
    TensorIteratorMergedInputDesc,
    TensorIteratorInvariantInputDesc,
    TensorIteratorBodyOutputDesc,
    TensorIteratorConcatOutputDesc,
)
from openvino.runtime.utils.types import (
    NodeInput,
    NumericData,
    NumericType,
    ScalarData,
    TensorShape,
    as_node,
    as_nodes,
    get_dtype,
    get_element_type,
    get_element_type_str,
    make_constant_node,
)

_get_node_factory_opset8 = partial(_get_node_factory, "opset8")


# -------------------------------------------- ops ------------------------------------------------


@nameable_op
def deformable_convolution(
        data: NodeInput,
        offsets: NodeInput,
        filters: NodeInput,
        strides: List[int],
        pads_begin: List[int],
        pads_end: List[int],
        dilations: List[int],
        mask: Optional[NodeInput] = None,
        auto_pad: str = "EXPLICIT",
        group: int = 1,
        deformable_group: int = 1,
        bilinear_interpolation_pad: bool = False,
        name: Optional[str] = None,
) -> Node:
    """Return a node which performs deformable convolution operation.

    @param data: The node providing data batch tensor.
    @param offsets: The node providing offset tensor.
    @param filters: The node providing filters tensor.
    @param strides: The distance (in pixels) to slide the filter on the feature map over the axes.
    @param pads_begin: The number of pixels to add to the beginning along each axis.
    @param pads_end: The number of pixels to add to the end along each axis.
    @param dilations: The distance in width and height between elements (weights) in the filter.
    @param mask: The node providing modulation scalar (mask) tensor.
    @param auto_pad: The type of padding. Range of values: explicit, same_upper, same_lower, valid.
    @param group: The number of groups which both output and input should be split into.
    @param deformable_group: The number of groups which deformable values and output should be split
                             into along the channel axis.
    @param bilinear_interpolation_pad: The flag that determines the mode of bilinear interpolation
                                               execution.
    @param name: The optional new name for output node.
    @return New node performing deformable convolution operation.
    """
    if mask is None:
        inputs = as_nodes(data, offsets, filters)
    else:
        inputs = as_nodes(data, offsets, filters, mask)

    return _get_node_factory_opset8().create(
        "DeformableConvolution",
        inputs,
        {
            "strides": strides,
            "pads_begin": pads_begin,
            "pads_end": pads_end,
            "dilations": dilations,
            "auto_pad": auto_pad,
            "group": group,
            "deformable_group": deformable_group,
            "bilinear_interpolation_pad": bilinear_interpolation_pad
        },
    )


@nameable_op
def adaptive_avg_pool(
        data: NodeInput,
        output_shape: NodeInput
) -> Node:
    """Return a node which performs AdaptiveAvgPool operation.

    @param data: The list of input nodes
    @param output_shape: the shape of spatial dimentions after operation
    @return: The new node performing AdaptiveAvgPool operation on the data
    """
    inputs = as_nodes(data, output_shape)
    return _get_node_factory_opset8().create("AdaptiveAvgPool", inputs)


@nameable_op
def adaptive_max_pool(
        data: NodeInput,
        output_shape: NodeInput,
        index_element_type: str = "i64"
) -> Node:
    """Return a node which performs AdaptiveMaxPool operation.

    @param data: The list of input nodes
    @param output_shape: the shape of spatial dimentions after operation
    @param index_element_type: Type of indices output.
    @return: The new node performing AdaptiveMaxPool operation on the data
    """
    inputs = as_nodes(data, output_shape)

    attributes = {
        "index_element_type": index_element_type,
    }

    return _get_node_factory_opset8().create("AdaptiveMaxPool", inputs, attributes)


@nameable_op
def multiclass_nms(
    boxes: NodeInput,
    scores: NodeInput,
    sort_result_type: str = "none",
    sort_result_across_batch: bool = False,
    output_type: str = "i64",
    iou_threshold: float = 0.0,
    score_threshold: float = 0.0,
    nms_top_k: int = -1,
    keep_top_k: int = -1,
    background_class: int = -1,
    nms_eta: float = 1.0,
    normalized: bool = True
) -> Node:
    """Return a node which performs MulticlassNms.

    @param boxes: Tensor with box coordinates.
    @param scores: Tensor with box scores.
    @param sort_result_type: Specifies order of output elements, possible values:
                             'class': sort selected boxes by class id (ascending)
                             'score': sort selected boxes by score (descending)
                             'none': do not guarantee the order.
    @param sort_result_across_batch: Specifies whenever it is necessary to sort selected boxes
                                     across batches or not
    @param output_type: Specifies the output tensor type, possible values:
                        'i64', 'i32'
    @param iou_threshold: Specifies intersection over union threshold
    @param score_threshold: Specifies minimum score to consider box for the processing
    @param nms_top_k: Specifies maximum number of boxes to be selected per class, -1 meaning
                      to keep all boxes
    @param keep_top_k: Specifies maximum number of boxes to be selected per batch element, -1
                       meaning to keep all boxes
    @param background_class: Specifies the background class id, -1 meaning to keep all classes
    @param nms_eta: Specifies eta parameter for adpative NMS, in close range [0, 1.0]
    @param normalized: Specifies whether boxes are normalized or not
    @return: The new node which performs MuticlassNms
    """
    inputs = as_nodes(boxes, scores)

    attributes = {
        "sort_result_type": sort_result_type,
        "sort_result_across_batch": sort_result_across_batch,
        "output_type": output_type,
        "iou_threshold": iou_threshold,
        "score_threshold": score_threshold,
        "nms_top_k": nms_top_k,
        "keep_top_k": keep_top_k,
        "background_class": background_class,
        "nms_eta": nms_eta,
        "normalized": normalized
    }

    return _get_node_factory_opset8().create("MulticlassNms", inputs, attributes)


@nameable_op
def matrix_nms(
    boxes: NodeInput,
    scores: NodeInput,
    sort_result_type: str = "none",
    sort_result_across_batch: bool = False,
    output_type: str = "i64",
    score_threshold: float = 0.0,
    nms_top_k: int = -1,
    keep_top_k: int = -1,
    background_class: int = -1,
    decay_function: str = "linear",
    gaussian_sigma: float = 2.0,
    post_threshold: float = 0.0,
    normalized: bool = True
) -> Node:
    """Return a node which performs MatrixNms.

    @param boxes: Tensor with box coordinates.
    @param scores: Tensor with box scores.
    @param sort_result_type: Specifies order of output elements, possible values:
                             'class': sort selected boxes by class id (ascending)
                             'score': sort selected boxes by score (descending)
                             'none': do not guarantee the order.
    @param sort_result_across_batch: Specifies whenever it is necessary to sort selected boxes
                                     across batches or not
    @param output_type: Specifies the output tensor type, possible values:
                        'i64', 'i32'
    @param score_threshold: Specifies minimum score to consider box for the processing
    @param nms_top_k: Specifies maximum number of boxes to be selected per class, -1 meaning
                      to keep all boxes
    @param keep_top_k: Specifies maximum number of boxes to be selected per batch element, -1
                       meaning to keep all boxes
    @param background_class: Specifies the background class id, -1 meaning to keep all classes
    @param decay_function: Specifies decay function used to decay scores, possible values:
                           'gaussian', 'linear'
    @param gaussian_sigma: Specifies gaussian_sigma parameter for gaussian decay_function
    @param post_threshold: Specifies threshold to filter out boxes with low confidence score
                           after decaying
    @param normalized: Specifies whether boxes are normalized or not
    @return: The new node which performs MatrixNms
    """
    inputs = as_nodes(boxes, scores)

    attributes = {
        "sort_result_type": sort_result_type,
        "sort_result_across_batch": sort_result_across_batch,
        "output_type": output_type,
        "score_threshold": score_threshold,
        "nms_top_k": nms_top_k,
        "keep_top_k": keep_top_k,
        "background_class": background_class,
        "decay_function": decay_function,
        "gaussian_sigma": gaussian_sigma,
        "post_threshold": post_threshold,
        "normalized": normalized
    }

    return _get_node_factory_opset8().create("MatrixNms", inputs, attributes)


@nameable_op
def gather(
        data: NodeInput,
        indices: NodeInput,
        axis: NodeInput,
        batch_dims: Optional[int] = 0,
) -> Node:
    """Return a node which performs Gather with support of negative indices.

    @param data:         N-D tensor with data for gathering
    @param indices:      N-D tensor with indices by which data is gathered. Negative indices
    indicate reverse indexing from the end
    @param axis:         axis along which elements are gathered
    @param batch_dims:   number of batch dimensions
    @return:             The new node which performs Gather
    """
    inputs = as_nodes(data, indices, axis)
    attributes = {
        "batch_dims": batch_dims
    }
    return _get_node_factory_opset8().create("Gather", inputs, attributes)


@nameable_op
def max_pool(
    data: NodeInput,
    strides: List[int],
    dilations: List[int],
    pads_begin: List[int],
    pads_end: List[int],
    kernel_shape: TensorShape,
    rounding_type: str = "floor",
    auto_pad: Optional[str] = None,
    index_element_type: Optional[str] = "i64",
    axis: Optional[int] = 0,
    name: Optional[str] = None,
) -> Node:
    """Perform max pooling operation and return both values and indices of the selected elements.

    @param  data:                The node providing input data.
    @param  strides:             The distance (in pixels) to slide the filter on the feature map
                                 over the axes.
    @param  dilations:           The dilation of filter elements(distance between elements).
    @param  pads_begin:          The number of pixels to add at the beginning along each axis.
    @param  pads_end:            The number of pixels to add at the end along each axis.
    @param  kernel_shape:        The pooling operation kernel shape.
    @param  rounding_type:       Determines used rounding schema when computing output shape.
                                 Acceptable values are: ['floor', 'ceil']. Defaults to 'floor'.
    @param  auto_pad:            Determines how the padding is calculated. Acceptable values:
                                 [None, 'same_upper', 'same_lower', 'valid']. Defaults to None.
    @param  index_element_type:  The data type used for the indices output of this operator.
                                 Defaults to i64.
    @param  axis:                The first dimension in the data shape used to determine the maximum
                                 returned index value. The value is the product of all dimensions
                                 starting at the provided axis. Defaults to 0.
    @param  name:                The optional name for the created output node.

    @return   The new node performing max pooling operation.
    """
    if auto_pad is None:
        auto_pad = "explicit"
    return _get_node_factory_opset8().create(
        "MaxPool",
        [as_node(data)],
        {
            "strides": strides,
            "dilations": dilations,
            "pads_begin": pads_begin,
            "pads_end": pads_end,
            "kernel": kernel_shape,
            "rounding_type": rounding_type.upper(),
            "auto_pad": auto_pad.upper(),
            "index_element_type": index_element_type,
            "axis": axis,
        },
    )


@nameable_op
def random_uniform(
        output_shape: NodeInput,
        min_val: NodeInput,
        max_val: NodeInput,
        output_type: str,
        global_seed: int = 0,
        op_seed: int = 0
) -> Node:
    """Return a node which generates sequence of random values from uniform distribution.

    @param output_shape: Tensor with shape of the output tensor.
    @param min_val: Tensor with the lower bound on the range of random values to generate.
    @param max_val: Tensor with the upper bound on the range of random values to generate.
    @param output_type: Specifies the output tensor type, possible values:
    'i64', 'i32', 'f64', 'f32', 'f16', 'bf16'.
    @param global_seed: Specifies global seed value. Required to be a positive integer or 0.
    @param op_seed: Specifies operational seed value. Required to be a positive integer or 0.
    @return The new node which performs generation of random values from uniform distribution.
    """
    inputs = as_nodes(output_shape, min_val, max_val)

    if global_seed < 0:
        raise RuntimeError("global_seed should be positive or 0. Got: {}".format(global_seed))

    if op_seed < 0:
        raise RuntimeError("op_seed should be positive or 0. Got: {}".format(op_seed))

    attributes = {
        "output_type": output_type,
        "global_seed": global_seed,
        "op_seed": op_seed,
    }
    return _get_node_factory_opset8().create("RandomUniform", inputs, attributes)


@nameable_op
def if_op(
        condition: NodeInput,
        inputs: List[Node],
        bodies: Tuple[GraphBody, GraphBody],
        input_desc: Tuple[List[TensorIteratorInvariantInputDesc], List[TensorIteratorInvariantInputDesc]],
        output_desc: Tuple[List[TensorIteratorBodyOutputDesc], List[TensorIteratorBodyOutputDesc]],
        name: Optional[str] = None,
) -> Node:
    """Execute one of the bodies depending on condtion value.

    @param      condition:             A scalar or 1D tensor with 1 element specifying body will be executed.
                                       If condition is True, then body will be executed, False - else_body.
    @param      inputs:                The provided inputs to If operation.
    @param      bodies:                Two graphs (then_body, else_body) which will be executed depending on
                                       condition value.
    @param      input_desc             Two lists (for then_body and else_body) which contain rules how If
                                       inputs are connected with body parameters.
    @param      output_desc:           Two lists (for then_body and else_body) which contain rules how If
                                       outputs are connected with body results.
    @param      name:                  The optional name for the created output node.

    @return: The new node which performs If operation.
    """
    attributes = {
        "then_body": bodies[0].serialize(),
        "else_body": bodies[1].serialize(),
        "then_inputs": {"invariant_input_desc": [desc.serialize() for desc in input_desc[0]]},
        "else_inputs": {"invariant_input_desc": [desc.serialize() for desc in input_desc[1]]},
        "then_outputs": {"body_output_desc": [desc.serialize() for desc in output_desc[0]]},
        "else_outputs": {"body_output_desc": [desc.serialize() for desc in output_desc[1]]}
    }
    return _get_node_factory_opset8().create("If", as_nodes(condition, *inputs),
                                             attributes)


@nameable_op
def slice(
        data: NodeInput,
        start: NodeInput,
        stop: NodeInput,
        step: NodeInput,
        axes: Optional[NodeInput] = None,
        name: Optional[str] = None,
) -> Node:
    """Return a node which generates Slice operation.

    @param  data: The node providing input data.
    @param  start: The node providing start indices (inclusively).
    @param  stop: The node providing stop indices (exclusively).
    @param  step: The node providing step values.
    @param  axes: The optional node providing axes to slice, default [0, 1, ..., len(start)-1].
    @param  name: The optional name for the created output node.
    @return The new node performing Slice operation.
    """
    if axes is None:
        inputs = as_nodes(data, start, stop, step)
    else:
        inputs = as_nodes(data, start, stop, step, axes)

    return _get_node_factory_opset8().create("Slice", inputs)


@nameable_op
def gather_nd(
        data: NodeInput,
        indices: NodeInput,
        batch_dims: Optional[int] = 0,
        name: Optional[str] = None,
) -> Node:
    """Return a node which performs GatherND.

    @param data:       N-D tensor with data for gathering
    @param indices:    K-D tensor of tuples with indices by which data is gathered
    @param batch_dims: Scalar value of batch dimensions
    @return: The new node which performs GatherND
    """
    inputs = as_nodes(data, indices)

    attributes = {
        "batch_dims": batch_dims
    }

    return _get_node_factory_opset8().create("GatherND", inputs, attributes)


@nameable_op
def prior_box(
    layer_shape: Node, image_shape: NodeInput, attrs: dict, name: Optional[str] = None
) -> Node:
    """Generate prior boxes of specified sizes and aspect ratios across all dimensions.

    @param  layer_shape:  Shape of layer for which prior boxes are computed.
    @param  image_shape:  Shape of image to which prior boxes are scaled.
    @param  attrs:        The dictionary containing key, value pairs for attributes.
    @param  name:         Optional name for the output node.
    @return Node representing prior box operation.
    Available attributes are:
    * min_size                      The minimum box size (in pixels).
                                    Range of values: positive floating point numbers
                                    Default value: []
                                    Required: no
    * max_size                      The maximum box size (in pixels).
                                    Range of values: positive floating point numbers
                                    Default value: []
                                    Required: no
    * aspect_ratio                  Aspect ratios of prior boxes.
                                    Range of values: set of positive floating point numbers
                                    Default value: []
                                    Required: no
    * flip                          The flag that denotes that each aspect_ratio is duplicated and flipped.
                                    Range of values: {True, False}
                                    Default value: False
                                    Required: no
    * clip                          The flag that denotes if each value in the output tensor should be clipped
                                    to [0,1] interval.
                                    Range of values: {True, False}
                                    Default value: False
                                    Required: no
    * step                          The distance between box centers.
                                    Range of values: floating point non-negative number
                                    Default value: 0
                                    Required: no
    * offset                        This is a shift of box respectively to top left corner.
                                    Range of values: floating point non-negative number
                                    Default value: None
                                    Required: yes
    * variance                      The variance denotes a variance of adjusting bounding boxes. The attribute
                                    could contain 0, 1 or 4 elements.
                                    Range of values: floating point positive numbers
                                    Default value: []
                                    Required: no
    * scale_all_sizes               The flag that denotes type of inference.
                                    Range of values: False - max_size is ignored
                                                     True  - max_size is used
                                    Default value: True
                                    Required: no
    * fixed_ratio                   This is an aspect ratio of a box.
                                    Range of values: a list of positive floating-point numbers
                                    Default value: None
                                    Required: no
    * fixed_size                    This is an initial box size (in pixels).
                                    Range of values: a list of positive floating-point numbers
                                    Default value: None
                                    Required: no
    * density                       This is the square root of the number of boxes of each type.
                                    Range of values: a list of positive floating-point numbers
                                    Default value: None
                                    Required: no
    * min_max_aspect_ratios_order   The flag that denotes the order of output prior box.
                                    Range of values: False - the output prior box is in order of
                                                             [min, aspect_ratios, max]
                                                     True  - the output prior box is in order of
                                                             [min, max, aspect_ratios]
                                    Default value: True
                                    Required: no
    Example of attribute dictionary:
    @code{.py}
        # just required ones
        attrs = {
            'offset': 85,
        }
        attrs = {
            'offset': 85,
            'flip': True,
            'clip': True,
            'fixed_size': [32, 64, 128]
        }
    @endcode
    Optional attributes which are absent from dictionary will be set with corresponding default.
    """
    requirements = [
        ("offset", True, np.floating, is_non_negative_value),
        ("min_size", False, np.floating, is_positive_value),
        ("max_size", False, np.floating, is_positive_value),
        ("aspect_ratio", False, np.floating, is_positive_value),
        ("flip", False, np.bool_, None),
        ("clip", False, np.bool_, None),
        ("step", False, np.floating, is_non_negative_value),
        ("variance", False, np.floating, is_positive_value),
        ("scale_all_sizes", False, np.bool_, None),
        ("fixed_ratio", False, np.floating, is_positive_value),
        ("fixed_size", False, np.floating, is_positive_value),
        ("density", False, np.floating, is_positive_value),
        ("min_max_aspect_ratios_order", False, np.bool_, None),
    ]

    check_valid_attributes("PriorBox", attrs, requirements)

    return _get_node_factory_opset8().create("PriorBox", [layer_shape, as_node(image_shape)], attrs)


@nameable_op
def i420_to_bgr(
        arg: NodeInput,
        arg_u: Optional[NodeInput] = None,
        arg_v: Optional[NodeInput] = None,
        name: Optional[str] = None,
) -> Node:
    """Return a node which performs I420toBGR operation.

    @param  arg: The node providing single or Y plane data.
    @param  arg_u: The node providing U plane data. Required for separate planes.
    @param  arg_v: The node providing V plane data. Required for separate planes.
    @param  name: The optional name for the created output node.
    @return The new node performing I420toBGR operation.
    """
    if arg_u is None and arg_v is None:
        inputs = as_nodes(arg)
    elif arg_u is not None and arg_v is not None:
        inputs = as_nodes(arg, arg_u, arg_v)
    else:
        raise UserInputError(
            "Operation I420toBGR must have one (single plane) or three (separate planes) inputs provided."
        )

    return _get_node_factory_opset8().create("I420toBGR", inputs)


@nameable_op
def i420_to_rgb(
        arg: NodeInput,
        arg_u: Optional[NodeInput] = None,
        arg_v: Optional[NodeInput] = None,
        name: Optional[str] = None,
) -> Node:
    """Return a node which performs I420toRGB operation.

    @param  arg: The node providing single or Y plane data.
    @param  arg_u: The node providing U plane data. Required for separate planes.
    @param  arg_v: The node providing V plane data. Required for separate planes.
    @param  name: The optional name for the created output node.
    @return The new node performing I420toRGB operation.
    """
    if arg_u is None and arg_v is None:
        inputs = as_nodes(arg)
    elif arg_u is not None and arg_v is not None:
        inputs = as_nodes(arg, arg_u, arg_v)
    else:
        raise UserInputError(
            "Operation I420toRGB must have one (single plane) or three (separate planes) inputs provided."
        )

    return _get_node_factory_opset8().create("I420toRGB", inputs)


@nameable_op
def nv12_to_bgr(
        arg: NodeInput,
        arg_uv: Optional[NodeInput] = None,
        name: Optional[str] = None,
) -> Node:
    """Return a node which performs NV12toBGR operation.

    @param  arg: The node providing single or Y plane data.
    @param  arg_uv: The node providing UV plane data. Required for separate planes.
    @param  name: The optional name for the created output node.
    @return The new node performing NV12toBGR operation.
    """
    if arg_uv is None:
        inputs = as_nodes(arg)
    else:
        inputs = as_nodes(arg, arg_uv)

    return _get_node_factory_opset8().create("NV12toBGR", inputs)


@nameable_op
def nv12_to_rgb(
        arg: NodeInput,
        arg_uv: Optional[NodeInput] = None,
        name: Optional[str] = None,
) -> Node:
    """Return a node which performs NV12toRGB operation.

    @param  arg: The node providing single or Y plane data.
    @param  arg_uv: The node providing UV plane data. Required for separate planes.
    @param  name: The optional name for the created output node.
    @return The new node performing NV12toRGB operation.
    """
    if arg_uv is None:
        inputs = as_nodes(arg)
    else:
        inputs = as_nodes(arg, arg_uv)

    return _get_node_factory_opset8().create("NV12toRGB", inputs)