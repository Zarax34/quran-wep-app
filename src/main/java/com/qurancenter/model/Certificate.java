package com.qurancenter.model;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "certificate")
public class Certificate {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "student_id", nullable = false)
    private Integer studentId;

    @ManyToOne
    @JoinColumn(name = "student_id", insertable = false, updatable = false)
    private Student student;

    @Column(name = "course_id", nullable = false)
    private Integer courseId;

    @ManyToOne
    @JoinColumn(name = "course_id", insertable = false, updatable = false)
    private Course courseInfo;

    @Column(name = "issue_date")
    private LocalDateTime issueDate = LocalDateTime.now();

    @Column(name = "certificate_file", length = 255)
    private String certificateFile;

    @Column(name = "certificate_url", length = 500)
    private String certificateUrl;
}
