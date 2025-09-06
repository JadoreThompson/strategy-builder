"use client";

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Lightbulb, Scale, Sword } from "lucide-react";
import { Link } from "react-router";

const DashboardSidebar = ({}: {}) => {
  const path = window.location.pathname.split("/")[1];

  return (
    <Sidebar className="transition-all">
      <SidebarHeader>
        <Link to="/" className="flex items-center gap-2 font-semibold">
          <Scale className="h-6 w-6" />
          StratBuilder
        </Link>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {(
                [
                  ["strategies", Lightbulb],
                  ["positions", Sword],
                ] as [string, React.ForwardRefExoticComponent<any>][]
              ).map(([val, I]) => (
                <SidebarMenuItem>
                  <SidebarMenuButton asChild>
                    <Link
                      to={`/${val}`}
                      className={`flex items-center gap-2 ${
                        path === val ? "bg-gray-300/20 font-medium" : ""
                      }`}
                    >
                      <I className="h-4 w-4 font-bold" />
                      {val.charAt(0).toUpperCase() + val.slice(1)}
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
};

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="w-full min-h-screen flex">
      <SidebarProvider>
        <DashboardSidebar />
        <main className="flex-1">
          <SidebarTrigger />
          <div className="max-w-7xl mx-auto mt-7">{children}</div>
        </main>
      </SidebarProvider>
    </div>
  );
}
