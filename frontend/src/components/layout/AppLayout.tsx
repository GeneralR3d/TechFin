import { Outlet, useLocation } from "react-router-dom";
import { TopNav } from "./TopNav";
import { FirstLoginDialog } from "@/components/onboarding/FirstLoginDialog";

export function AppLayout() {
  const location = useLocation();
  return (
    <>
      <TopNav />
      <FirstLoginDialog />
      <Outlet key={location.key} />
    </>
  );
}
