export type GeminiPart =
  | {
      text: string;
    }
  | {
      inlineData: {
        data: string;
        mimeType: string;
      };
    }
  | {
      fileData: {
        fileUri: string;
        mimeType: string;
      };
    };
