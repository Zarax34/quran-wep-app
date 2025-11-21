package com.qurancenter.model;

import jakarta.persistence.*;
import lombok.Data;

@Data
@Entity
@Table(name = "settings")
public class Settings {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "site_name", length = 100)
    private String siteName = "مركز الإمام حفص";

    @Column(name = "site_description", length = 200)
    private String siteDescription = "لتعليم القرآن الكريم";

    @Column(name = "contact_phone", length = 20)
    private String contactPhone;

    @Column(name = "contact_email", length = 100)
    private String contactEmail;

    @Column(name = "location_address", length = 300)
    private String locationAddress = "مأرب - شارع الأربعين - خلف مستشفى نيوم";

    @Column(name = "location_map_url", length = 500)
    private String locationMapUrl;

    @Column(length = 200)
    private String logo;

    @Column(name = "primary_color", length = 7)
    private String primaryColor = "#2c5aa0";

    @Column(name = "secondary_color", length = 7)
    private String secondaryColor = "#28a745";

    @Column(name = "background_color", length = 7)
    private String backgroundColor = "#f8f9fa";

    @Column(name = "text_color", length = 7)
    private String textColor = "#2c3e50";

    @Column(name = "whatsapp_message_template", columnDefinition = "TEXT")
    private String whatsappMessageTemplate = "تقرير {report_type} للتسميع\n\nالطالب: {student_name}\nالحلقة: {circle_name}\nالمعلم: {teacher_name}\nالفترة: من {start_date} إلى {end_date}\n\nالتسميع:\n{reports_details}\n\nإحصائيات الحضور:\n{attendance_stats}\n\n{site_name}";

    @Column(name = "support_bank_accounts", columnDefinition = "TEXT")
    private String supportBankAccounts = "بنك الكريمي: 123456789\nبنك الشرق: 987654321\nبنك التضامن: 456789123";

    @Column(name = "support_message", columnDefinition = "TEXT")
    private String supportMessage = "نورٌ نُهديه وجيل نربيه";

    @Column(name = "dark_mode_enabled")
    private Boolean darkModeEnabled = false;

    @Column(name = "teacher_requires_approval")
    private Boolean teacherRequiresApproval = true;

    @Column(name = "allow_custom_teacher_name")
    private Boolean allowCustomTeacherName = true;

    @Column(name = "social_instagram", length = 200)
    private String socialInstagram;

    @Column(name = "social_facebook", length = 200)
    private String socialFacebook;

    @Column(name = "social_whatsapp", length = 200)
    private String socialWhatsapp;

    @Column(name = "social_telegram", length = 200)
    private String socialTelegram;
}
