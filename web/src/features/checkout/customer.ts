import { useState } from "react";

const NAME_KEY = "balance-customer-name";
const PHONE_KEY = "balance-customer-phone";

/** Имя/телефон запоминаются между заказами. */
export function useCustomerForm() {
  const [name, setName] = useState(() => localStorage.getItem(NAME_KEY) ?? "");
  const [phone, setPhone] = useState(() => localStorage.getItem(PHONE_KEY) ?? "");
  const [comment, setComment] = useState("");
  const [touched, setTouched] = useState(false);

  const persist = (n: string, p: string) => {
    localStorage.setItem(NAME_KEY, n);
    localStorage.setItem(PHONE_KEY, p);
  };

  return { name, setName, phone, setPhone, comment, setComment, touched, setTouched, persist };
}

/** Грубая проверка телефона: минимум 5 цифр. */
export function isPhoneValid(phone: string): boolean {
  return (phone.match(/\d/g) ?? []).length >= 5;
}
