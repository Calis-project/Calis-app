export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export function toErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }

  return "Unexpected server error";
}
