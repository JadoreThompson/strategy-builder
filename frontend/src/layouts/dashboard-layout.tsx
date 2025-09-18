"use client";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Lightbulb, Scale, UserRoundPlus } from "lucide-react";
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
                  ["accounts", UserRoundPlus],
                ] as [string, React.ForwardRefExoticComponent<any>][]
              ).map(([val, I]) => (
                <SidebarMenuItem key={val}>
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
      <SidebarFooter></SidebarFooter>
    </Sidebar>
  );
};

export function DashboardLayout({
  children,
  className = "max-w-7xl mx-auto mt-7",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className="flex min-h-screen w-full">
      <SidebarProvider>
        <DashboardSidebar />
        <main className="flex-1 pb-5">
          <SidebarTrigger />
          <div className={className}>{children}</div>
        </main>
      </SidebarProvider>
    </div>
  );
}
