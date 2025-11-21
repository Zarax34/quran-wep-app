package com.qurancenter.security;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class HashTest {

    @Test
    public void testHash() {
        FlaskPasswordEncoder encoder = new FlaskPasswordEncoder();
        String raw = "admin123";
        String encoded = "pbkdf2:sha256:600000$di1mLHDTYlv2yH21$7c23c33c8c9a5f95415ba1496fa423312e1ce2c777e424e2007fc186ef0ff7a5";
        boolean matches = encoder.matches(raw, encoded);
        System.out.println("Matches: " + matches);
        if (!matches) {
            throw new RuntimeException("Hash mismatch!");
        }
    }
}
