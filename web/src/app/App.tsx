import { Navigate, Route, Routes } from "react-router-dom";
import { UiShowcase } from "../dev/UiShowcase";
import { hasSeenWelcome } from "../features/cart/store";
import { CheckoutPage } from "../features/checkout/CheckoutPage";
import { DrinkPage } from "../features/menu/DrinkPage";
import { MenuPage } from "../features/menu/MenuPage";
import { OrdersPage } from "../features/orders/OrdersPage";
import { StartPage } from "../features/welcome/StartPage";
import { useT } from "../shared/i18n";
import { HealthPage } from "./pages/HealthPage";

function Stub({ text }: { text: string }) {
  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-[480px] items-center justify-center bg-bg p-10 text-center text-text">
      <p className="text-sm text-text-2">{text}</p>
    </main>
  );
}

export function App() {
  const t = useT();
  const seen = hasSeenWelcome();
  return (
    <Routes>
      <Route path="/" element={seen ? <Navigate to="/menu" replace /> : <StartPage />} />
      <Route path="/menu" element={<MenuPage />} />
      <Route path="/drink/:id" element={<DrinkPage />} />
      <Route path="/checkout" element={<CheckoutPage />} />
      <Route path="/orders" element={<OrdersPage />} />
      <Route path="/order/:id" element={<OrdersPage />} />
      <Route path="/bonus" element={<Stub text={t.bonusSoon} />} />
      <Route path="/profile" element={<Stub text={t.profileSoon} />} />
      <Route path="/health" element={<HealthPage />} />
      {import.meta.env.DEV ? <Route path="/dev/ui" element={<UiShowcase />} /> : null}
    </Routes>
  );
}
