package com.qurancenter.model;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDate;

@Data
@Entity
@Table(name = "student")
public class Student {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(nullable = false, length = 100)
    private String name;

    private Integer age;

    @Column(name = "student_phone", length = 20)
    private String studentPhone;

    @Column(name = "parent_phone", length = 20)
    private String parentPhone;

    @Column(name = "parent_id")
    private Integer parentId;

    @ManyToOne
    @JoinColumn(name = "parent_id", insertable = false, updatable = false)
    private Parent parent;

    @Column(name = "circle_id")
    private Integer circleId;

    @ManyToOne
    @JoinColumn(name = "circle_id", insertable = false, updatable = false)
    private Circle circle;

    @Column(name = "is_active")
    private Boolean isActive = true;

    @Column(length = 200)
    private String photo;

    @Column(name = "academic_year", length = 10)
    private String academicYear = "2025";

    @Column(name = "pending_approval")
    private Boolean pendingApproval = true;

    @Column(name = "last_recitation_date")
    private LocalDate lastRecitationDate;

    @Column(name = "total_verses_since_year_start")
    private Integer totalVersesSinceYearStart = 0;

    @Column(name = "current_address", length = 200)
    private String currentAddress;

    @Column(name = "previous_address", length = 200)
    private String previousAddress;

    @Column(length = 100)
    private String governorate;

    @Column(name = "date_of_birth")
    private LocalDate dateOfBirth;

    @Column(name = "previous_memorization", length = 200)
    private String previousMemorization;

    @Column(name = "enrollment_date")
    private LocalDate enrollmentDate = LocalDate.now();

    @Column(name = "last_memorized_sura", length = 100)
    private String lastMemorizedSura = "الفاتحة";

    @Column(name = "last_memorized_ayah")
    private Integer lastMemorizedAyah = 0;

    @Column(name = "memorization_direction", length = 50)
    private String memorizationDirection = "BaqarahToNas";

    @Column(name = "parent_relationship", length = 50)
    private String parentRelationship = "أب";
}
