import { Calendar, ListTodo } from "lucide-react";
import { NavLink } from "./NavLink";
import { cn } from "@/lib/utils";

export function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 glass-effect border-t border-border/50">
      <div className="flex items-center justify-around h-20 max-w-2xl mx-auto px-8">
        <NavLink
          to="/"
          end
          className="flex flex-col items-center justify-center gap-2 px-8 py-2 rounded-xl transition-all duration-300 relative"
          activeClassName="text-foreground"
        >
          {({ isActive }) => (
            <>
              {isActive && (
                <div className="absolute inset-0 bg-muted rounded-xl" />
              )}
              <Calendar className="h-6 w-6 relative z-10" />
              <span className="text-xs font-semibold relative z-10">Slots</span>
            </>
          )}
        </NavLink>
        
        <NavLink
          to="/workflows"
          className="flex flex-col items-center justify-center gap-2 px-8 py-2 rounded-xl transition-all duration-300 relative"
          activeClassName="text-foreground"
        >
          {({ isActive }) => (
            <>
              {isActive && (
                <div className="absolute inset-0 bg-muted rounded-xl" />
              )}
              <ListTodo className="h-6 w-6 relative z-10" />
              <span className="text-xs font-semibold relative z-10">Gaps</span>
            </>
          )}
        </NavLink>
      </div>
    </nav>
  );
}
