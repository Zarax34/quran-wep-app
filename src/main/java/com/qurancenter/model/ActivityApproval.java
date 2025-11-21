package com.qurancenter.model;

import jakarta.persistence.*;
import lombok.Data;

@Data
@Entity
@Table(name = "activity_approval")
public class ActivityApproval {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "student_id", nullable = false)
    private Integer studentId;

    @ManyToOne
    @JoinColumn(name = "student_id", insertable = false, updatable = false)
    private Student student;

    @Column(name = "activity_id", nullable = false)
    private Integer activityId;

    @ManyToOne
    @JoinColumn(name = "activity_id", insertable = false, updatable = false)
    private CenterActivity activity;

    @Column(length = 20)
    private String status = "Pending";
}
