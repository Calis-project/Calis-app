"use client";

import { UploadCloud } from "lucide-react";
import type { DragEvent, KeyboardEvent } from "react";
import { useRef, useState } from "react";

type FileDropProps = {
  accept: string;
  fileName?: string;
  label: string;
  subLabel: string;
  onFile: (file: File) => void;
};

export function FileDrop({
  accept,
  fileName,
  label,
  subLabel,
  onFile,
}: FileDropProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function openPicker() {
    inputRef.current?.click();
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files[0];

    if (file) {
      onFile(file);
    }
  }

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openPicker();
    }
  }

  return (
    <div
      className="file-drop"
      data-dragging={dragging}
      data-has-file={Boolean(fileName)}
      onClick={openPicker}
      onDragLeave={() => setDragging(false)}
      onDragOver={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDrop={onDrop}
      onKeyDown={onKeyDown}
      role="button"
      tabIndex={0}
    >
      <input
        accept={accept}
        hidden
        ref={inputRef}
        type="file"
        onChange={(event) => {
          const file = event.target.files?.[0];

          if (file) {
            onFile(file);
          }
          // Allow re-selecting the same file to fire change again.
          event.target.value = "";
        }}
      />
      <UploadCloud aria-hidden="true" size={24} strokeWidth={2} />
      <span>
        <strong>{fileName || label}</strong>
        <small>{fileName ? subLabel : accept}</small>
      </span>
    </div>
  );
}
