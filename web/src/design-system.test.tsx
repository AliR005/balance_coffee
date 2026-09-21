import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { activeStepIndex } from "./shared/lib/steps";
import { PriceText } from "./shared/ui/PriceText";
import { Stepper } from "./shared/ui/Stepper";

describe("PriceText", () => {
  it("formats kopeks as rubles", () => {
    render(<PriceText kopeks={32000} />);
    expect(screen.getByTestId("price").textContent).toContain("320");
  });

  it("rounds negative delta totals", () => {
    render(<PriceText kopeks={29000} />);
    expect(screen.getByTestId("price").textContent).toContain("290");
  });
});

describe("Stepper", () => {
  it("changes value within bounds", () => {
    let value = 1;
    const { rerender } = render(
      <Stepper label="Количество" value={value} onChange={(v) => (value = v)} />,
    );
    fireEvent.click(screen.getByLabelText("Больше"));
    expect(value).toBe(2);
    rerender(<Stepper label="Количество" value={value} onChange={(v) => (value = v)} />);
    fireEvent.click(screen.getByLabelText("Меньше"));
    expect(value).toBe(1);
  });

  it("disables buttons at bounds", () => {
    render(<Stepper label="Количество" value={1} min={1} max={1} onChange={() => {}} />);
    expect(screen.getByLabelText("Меньше")).toBeDisabled();
    expect(screen.getByLabelText("Больше")).toBeDisabled();
  });
});

describe("activeStepIndex", () => {
  const steps = [
    { title: "Эспрессо", atSec: 0 },
    { title: "Молоко", atSec: 3 },
    { title: "Рисунок", atSec: 6 },
  ];

  it("highlights steps by time", () => {
    expect(activeStepIndex(0, steps, 9)).toBe(0);
    expect(activeStepIndex(4, steps, 9)).toBe(1);
    expect(activeStepIndex(8, steps, 9)).toBe(2);
  });

  it("loops with duration", () => {
    expect(activeStepIndex(10, steps, 9)).toBe(0);
  });

  it("returns -1 without steps", () => {
    expect(activeStepIndex(1, [], 9)).toBe(-1);
  });
});
