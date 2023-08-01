import { CodeEditor } from "../components/code-editor";
import { FormFieldError } from "../screens/edit-form-hook/form";
import { classNames } from "../utils/common";

type tOpsCodeEditor = {
  label: string;
  value?: string;
  onChange: (value?: string) => void;
  className?: string;
  error?: FormFieldError;
};

export const OpsCodeEditor = (props: tOpsCodeEditor) => {
  const { className, onChange, value, label, error } = props;

  return (
    <>
      <label className="block text-sm font-medium leading-6 text-gray-900">{label}</label>
      <CodeEditor
        onChange={onChange}
        value={value}
        className={classNames(className ?? "")}
        error={error}
      />
    </>
  );
};
