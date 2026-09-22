import { Component, type ReactNode } from "react";
import { ru } from "../i18n";

interface Props {
  children: ReactNode;
}

interface State {
  failed: boolean;
}

/** Последний рубеж: вместо белого экрана — понятная ошибка с перезагрузкой. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { failed: false };

  static getDerivedStateFromError(): State {
    return { failed: true };
  }

  render(): ReactNode {
    if (!this.state.failed) return this.props.children;
    return (
      <main className="mx-auto flex min-h-dvh w-full max-w-[480px] flex-col items-center justify-center gap-3 bg-bg p-10 text-center text-text">
        <p className="text-sm text-text-2">{ru.error}</p>
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="h-12 rounded-control bg-[var(--primary)] px-6 text-[15px] font-semibold text-on-primary"
        >
          {ru.retry}
        </button>
      </main>
    );
  }
}
