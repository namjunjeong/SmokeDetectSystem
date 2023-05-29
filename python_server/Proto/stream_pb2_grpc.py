# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from . import stream_pb2 as stream__pb2


class StreamingStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.ImgStream = channel.stream_stream(
                '/Streaming/ImgStream',
                request_serializer=stream__pb2.Image.SerializeToString,
                response_deserializer=stream__pb2.Result.FromString,
                )


class StreamingServicer(object):
    """Missing associated documentation comment in .proto file."""

    def ImgStream(self, request_iterator, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_StreamingServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'ImgStream': grpc.stream_stream_rpc_method_handler(
                    servicer.ImgStream,
                    request_deserializer=stream__pb2.Image.FromString,
                    response_serializer=stream__pb2.Result.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'Streaming', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Streaming(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def ImgStream(request_iterator,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.stream_stream(request_iterator, target, '/Streaming/ImgStream',
            stream__pb2.Image.SerializeToString,
            stream__pb2.Result.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)