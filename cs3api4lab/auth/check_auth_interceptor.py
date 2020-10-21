import http

import cs3
import grpc
import cs3.rpc.code_pb2 as cs3code


class CheckAuthInterceptor(grpc.UnaryUnaryClientInterceptor,
                           grpc.UnaryStreamClientInterceptor,
                           grpc.StreamUnaryClientInterceptor,
                           grpc.StreamStreamClientInterceptor):
    unauth_codes = {cs3code.CODE_UNAUTHENTICATED}

    def __init__(self, log, authenticator):
        self.log = log
        self.authenticator = authenticator

    def intercept_unary_unary(self, continuation, client_call_details, request):
        return self._intercept_call(continuation, client_call_details, request)

    def intercept_stream_unary(self, continuation, client_call_details, request_iterator):
        return self._intercept_call(continuation, client_call_details, request_iterator)

    def intercept_unary_stream(self, continuation, client_call_details, request):
        return self._intercept_call(continuation, client_call_details, request)

    def intercept_stream_stream(self, continuation, client_call_details, request_iterator):
        return self._intercept_call(continuation, client_call_details, request_iterator)

    def _intercept_call(self, continuation, client_call_details, request_or_iterator):
        response = continuation(client_call_details, request_or_iterator)
        self._check_result(response.code(), response.result())
        return response

    def _check_result(self, code, result):
        if result is not None and result.status is not None and result.status.code in self.unauth_codes:
            if self.log is not None:
                self.log.info("Refresh auth token")
            self.authenticator.refresh_token()
