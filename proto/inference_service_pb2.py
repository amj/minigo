# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: proto/inference_service.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='proto/inference_service.proto',
  package='minigo',
  syntax='proto3',
  serialized_pb=_b('\n\x1dproto/inference_service.proto\x12\x06minigo\"\x12\n\x10GetConfigRequest\"\\\n\x11GetConfigResponse\x12\x12\n\nboard_size\x18\x01 \x01(\x05\x12\x16\n\x0evirtual_losses\x18\x02 \x01(\x05\x12\x1b\n\x13games_per_inference\x18\x03 \x01(\x05\"\x14\n\x12GetFeaturesRequest\"P\n\x13GetFeaturesResponse\x12\x10\n\x08\x62\x61tch_id\x18\x01 \x01(\x05\x12\x10\n\x08\x66\x65\x61tures\x18\x02 \x03(\x02\x12\x15\n\rbyte_features\x18\x03 \x01(\x0c\"D\n\x11PutOutputsRequest\x12\x10\n\x08\x62\x61tch_id\x18\x01 \x01(\x05\x12\x0e\n\x06policy\x18\x02 \x03(\x02\x12\r\n\x05value\x18\x03 \x03(\x02\"\x14\n\x12PutOutputsResponse2\xe7\x01\n\x10InferenceService\x12\x42\n\tGetConfig\x12\x18.minigo.GetConfigRequest\x1a\x19.minigo.GetConfigResponse\"\x00\x12H\n\x0bGetFeatures\x12\x1a.minigo.GetFeaturesRequest\x1a\x1b.minigo.GetFeaturesResponse\"\x00\x12\x45\n\nPutOutputs\x12\x19.minigo.PutOutputsRequest\x1a\x1a.minigo.PutOutputsResponse\"\x00\x62\x06proto3')
)




_GETCONFIGREQUEST = _descriptor.Descriptor(
  name='GetConfigRequest',
  full_name='minigo.GetConfigRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=41,
  serialized_end=59,
)


_GETCONFIGRESPONSE = _descriptor.Descriptor(
  name='GetConfigResponse',
  full_name='minigo.GetConfigResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='board_size', full_name='minigo.GetConfigResponse.board_size', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='virtual_losses', full_name='minigo.GetConfigResponse.virtual_losses', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='games_per_inference', full_name='minigo.GetConfigResponse.games_per_inference', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=61,
  serialized_end=153,
)


_GETFEATURESREQUEST = _descriptor.Descriptor(
  name='GetFeaturesRequest',
  full_name='minigo.GetFeaturesRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=155,
  serialized_end=175,
)


_GETFEATURESRESPONSE = _descriptor.Descriptor(
  name='GetFeaturesResponse',
  full_name='minigo.GetFeaturesResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='batch_id', full_name='minigo.GetFeaturesResponse.batch_id', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='features', full_name='minigo.GetFeaturesResponse.features', index=1,
      number=2, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='byte_features', full_name='minigo.GetFeaturesResponse.byte_features', index=2,
      number=3, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=177,
  serialized_end=257,
)


_PUTOUTPUTSREQUEST = _descriptor.Descriptor(
  name='PutOutputsRequest',
  full_name='minigo.PutOutputsRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='batch_id', full_name='minigo.PutOutputsRequest.batch_id', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='policy', full_name='minigo.PutOutputsRequest.policy', index=1,
      number=2, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='value', full_name='minigo.PutOutputsRequest.value', index=2,
      number=3, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=259,
  serialized_end=327,
)


_PUTOUTPUTSRESPONSE = _descriptor.Descriptor(
  name='PutOutputsResponse',
  full_name='minigo.PutOutputsResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=329,
  serialized_end=349,
)

DESCRIPTOR.message_types_by_name['GetConfigRequest'] = _GETCONFIGREQUEST
DESCRIPTOR.message_types_by_name['GetConfigResponse'] = _GETCONFIGRESPONSE
DESCRIPTOR.message_types_by_name['GetFeaturesRequest'] = _GETFEATURESREQUEST
DESCRIPTOR.message_types_by_name['GetFeaturesResponse'] = _GETFEATURESRESPONSE
DESCRIPTOR.message_types_by_name['PutOutputsRequest'] = _PUTOUTPUTSREQUEST
DESCRIPTOR.message_types_by_name['PutOutputsResponse'] = _PUTOUTPUTSRESPONSE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

GetConfigRequest = _reflection.GeneratedProtocolMessageType('GetConfigRequest', (_message.Message,), dict(
  DESCRIPTOR = _GETCONFIGREQUEST,
  __module__ = 'proto.inference_service_pb2'
  # @@protoc_insertion_point(class_scope:minigo.GetConfigRequest)
  ))
_sym_db.RegisterMessage(GetConfigRequest)

GetConfigResponse = _reflection.GeneratedProtocolMessageType('GetConfigResponse', (_message.Message,), dict(
  DESCRIPTOR = _GETCONFIGRESPONSE,
  __module__ = 'proto.inference_service_pb2'
  # @@protoc_insertion_point(class_scope:minigo.GetConfigResponse)
  ))
_sym_db.RegisterMessage(GetConfigResponse)

GetFeaturesRequest = _reflection.GeneratedProtocolMessageType('GetFeaturesRequest', (_message.Message,), dict(
  DESCRIPTOR = _GETFEATURESREQUEST,
  __module__ = 'proto.inference_service_pb2'
  # @@protoc_insertion_point(class_scope:minigo.GetFeaturesRequest)
  ))
_sym_db.RegisterMessage(GetFeaturesRequest)

GetFeaturesResponse = _reflection.GeneratedProtocolMessageType('GetFeaturesResponse', (_message.Message,), dict(
  DESCRIPTOR = _GETFEATURESRESPONSE,
  __module__ = 'proto.inference_service_pb2'
  # @@protoc_insertion_point(class_scope:minigo.GetFeaturesResponse)
  ))
_sym_db.RegisterMessage(GetFeaturesResponse)

PutOutputsRequest = _reflection.GeneratedProtocolMessageType('PutOutputsRequest', (_message.Message,), dict(
  DESCRIPTOR = _PUTOUTPUTSREQUEST,
  __module__ = 'proto.inference_service_pb2'
  # @@protoc_insertion_point(class_scope:minigo.PutOutputsRequest)
  ))
_sym_db.RegisterMessage(PutOutputsRequest)

PutOutputsResponse = _reflection.GeneratedProtocolMessageType('PutOutputsResponse', (_message.Message,), dict(
  DESCRIPTOR = _PUTOUTPUTSRESPONSE,
  __module__ = 'proto.inference_service_pb2'
  # @@protoc_insertion_point(class_scope:minigo.PutOutputsResponse)
  ))
_sym_db.RegisterMessage(PutOutputsResponse)



_INFERENCESERVICE = _descriptor.ServiceDescriptor(
  name='InferenceService',
  full_name='minigo.InferenceService',
  file=DESCRIPTOR,
  index=0,
  options=None,
  serialized_start=352,
  serialized_end=583,
  methods=[
  _descriptor.MethodDescriptor(
    name='GetConfig',
    full_name='minigo.InferenceService.GetConfig',
    index=0,
    containing_service=None,
    input_type=_GETCONFIGREQUEST,
    output_type=_GETCONFIGRESPONSE,
    options=None,
  ),
  _descriptor.MethodDescriptor(
    name='GetFeatures',
    full_name='minigo.InferenceService.GetFeatures',
    index=1,
    containing_service=None,
    input_type=_GETFEATURESREQUEST,
    output_type=_GETFEATURESRESPONSE,
    options=None,
  ),
  _descriptor.MethodDescriptor(
    name='PutOutputs',
    full_name='minigo.InferenceService.PutOutputs',
    index=2,
    containing_service=None,
    input_type=_PUTOUTPUTSREQUEST,
    output_type=_PUTOUTPUTSRESPONSE,
    options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_INFERENCESERVICE)

DESCRIPTOR.services_by_name['InferenceService'] = _INFERENCESERVICE

# @@protoc_insertion_point(module_scope)
