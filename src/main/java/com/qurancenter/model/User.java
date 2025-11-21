package com.qurancenter.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.ToString;
import java.util.List;

@Data
@Entity
@Table(name = "user")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(unique = true, nullable = false, length = 80)
    private String username;

    @Column(nullable = false, length = 120)
    private String password;

    @Column(nullable = false, length = 20)
    private String role;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(unique = true, length = 120)
    private String email;

    @Column(name = "is_active")
    private Boolean isActive = true;

    @Column(name = "fingerprint_id", unique = true, length = 100)
    private String fingerprintId;

    @OneToMany(mappedBy = "teacher")
    @ToString.Exclude
    private List<Circle> circles;
}
