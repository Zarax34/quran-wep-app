package com.qurancenter.model;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "announcement")
public class Announcement {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(nullable = false, length = 200)
    private String title;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String content;

    @Column(length = 200)
    private String image;

    @Column(name = "date_posted")
    private LocalDateTime datePosted = LocalDateTime.now();

    @Column(name = "event_date")
    private LocalDate eventDate;

    @Column(name = "is_active")
    private Boolean isActive = true;
}
