import 'package:equatable/equatable.dart';

/// Generic API result wrapper for handling success and error states
sealed class ApiResult<T> extends Equatable {
  const ApiResult();

  @override
  List<Object?> get props => [];
}

/// Success state with data
class Success<T> extends ApiResult<T> {
  final T data;

  const Success(this.data);

  @override
  List<Object?> get props => [data];
}

/// Error state with message and optional error code
class Failure<T> extends ApiResult<T> {
  final String message;
  final int? statusCode;
  final dynamic error;

  const Failure({
    required this.message,
    this.statusCode,
    this.error,
  });

  @override
  List<Object?> get props => [message, statusCode, error];
}

/// Extension methods for easier result handling
extension ApiResultExtension<T> on ApiResult<T> {
  /// Returns data if success, null otherwise
  T? get dataOrNull {
    return switch (this) {
      Success(data: final data) => data,
      Failure() => null,
    };
  }

  /// Returns error message if failure, null otherwise
  String? get errorOrNull {
    return switch (this) {
      Success() => null,
      Failure(message: final message) => message,
    };
  }

  /// Execute callback when result is success
  void onSuccess(void Function(T data) callback) {
    if (this is Success<T>) {
      callback((this as Success<T>).data);
    }
  }

  /// Execute callback when result is failure
  void onFailure(void Function(String message) callback) {
    if (this is Failure<T>) {
      callback((this as Failure<T>).message);
    }
  }

  /// Map the data type
  ApiResult<R> map<R>(R Function(T data) transform) {
    return switch (this) {
      Success(data: final data) => Success(transform(data)),
      Failure(message: final msg, statusCode: final code, error: final err) =>
        Failure(message: msg, statusCode: code, error: err),
    };
  }
}
