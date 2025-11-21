package com.qurancenter.controller;

import com.qurancenter.model.Settings;
import com.qurancenter.repository.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import jakarta.servlet.http.HttpSession;
import java.util.Collections;

@Controller
public class MainController {

    @Autowired
    private SettingsRepository settingsRepository;
    @Autowired
    private UserRepository userRepository;
    @Autowired
    private StudentRepository studentRepository;
    @Autowired
    private CircleRepository circleRepository;
    @Autowired
    private ReportRepository reportRepository;

    @GetMapping("/")
    public String index(Authentication authentication) {
        if (authentication != null && authentication.isAuthenticated()) {
            String role = authentication.getAuthorities().stream()
                .findFirst().get().getAuthority();
            // Spring Security roles are usually ROLE_ADMIN, etc.
            // Our CustomUserDetailsService sets them.
            if (role.contains("PARENT")) {
                return "redirect:/parent_dashboard";
            }
            return "redirect:/dashboard";
        }
        return "redirect:/guest_dashboard";
    }

    @GetMapping("/login")
    public String login(Model model) {
        Settings settings = settingsRepository.findAll().stream().findFirst().orElse(new Settings());
        model.addAttribute("settings", settings);
        return "login";
    }

    @GetMapping("/guest_dashboard")
    public String guestDashboard(Model model) {
        Settings settings = settingsRepository.findAll().stream().findFirst().orElse(new Settings());
        model.addAttribute("settings", settings);
        return "guest_dashboard";
    }

    @GetMapping("/dashboard")
    public String dashboard(Model model, Authentication authentication, HttpSession session) {
         Settings settings = settingsRepository.findAll().stream().findFirst().orElse(new Settings());
         model.addAttribute("settings", settings);

         // Add stats
         model.addAttribute("total_students", studentRepository.count());
         // Count teachers (users with role='teacher')
         // Note: Repositories need to be updated to support count by role or we do filter.
         // For now, simple counts.
         model.addAttribute("total_teachers", 0); // Placeholder
         model.addAttribute("total_circles", circleRepository.count());
         model.addAttribute("recent_reports", Collections.emptyList()); // Placeholder

         // Set session attributes for view
         if (authentication != null) {
             session.setAttribute("name", authentication.getName());
             // Simplify role extraction
             String role = authentication.getAuthorities().stream().findFirst().get().getAuthority();
             session.setAttribute("role", role.replace("ROLE_", "").toLowerCase());
             session.setAttribute("user_id", 1); // Mock ID or fetch from DB
         }

         return "dashboard";
    }
}
