import { Box, Container, Typography, Grid } from '@mui/material';
import { keyframes } from '@mui/system';

const floatAnimation = keyframes`
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-15px) rotate(5deg); }
`;

const countUp = keyframes`
  0% { opacity: 0; transform: translateY(20px); }
  100% { opacity: 1; transform: translateY(0); }
`;

const stats = [
  { number: '100+', label: 'Projects Delivered' },
  { number: '50+', label: 'Happy Clients' },
  { number: '15+', label: 'AI Models Deployed' },
  { number: '99%', label: 'Client Satisfaction' },
];

const About = () => {
  return (
    <Box id="about" sx={{
      py: 12,
      background: 'linear-gradient(180deg, #132238 0%, #0B1426 50%, #132238 100%)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Subtle decorative elements */}
      <Box sx={{
        position: 'absolute', top: '20%', right: '5%',
        width: 200, height: 200,
        border: '1px solid rgba(100, 180, 255, 0.1)',
        borderRadius: '50%',
        animation: `${floatAnimation} 10s ease-in-out infinite`,
      }} />
      <Box sx={{
        position: 'absolute', bottom: '10%', left: '5%',
        width: 150, height: 150,
        border: '1px solid rgba(59, 130, 246, 0.1)',
        borderRadius: '30%',
        animation: `${floatAnimation} 8s ease-in-out infinite 1s`,
      }} />

      <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
        <Grid container spacing={6} alignItems="center">
          <Grid size={{ xs: 12, md: 6 }}>
            <Typography variant="overline" sx={{ color: '#64B4FF', letterSpacing: 3, fontWeight: 500 }}>
              About Us
            </Typography>
            <Typography variant="h2" sx={{
              fontSize: { xs: '2rem', md: '2.75rem' },
              fontWeight: 600,
              color: '#E2E8F0',
              mt: 1,
              mb: 3,
              letterSpacing: '-0.5px',
            }}>
              Pioneering Digital Excellence
            </Typography>
            <Typography sx={{ color: 'rgba(226,232,240,0.7)', lineHeight: 1.8, mb: 3 }}>
              At Yeda AI, we're passionate about leveraging technology to solve complex business challenges.
              Our team of experts combines deep technical expertise with industry knowledge to deliver
              solutions that drive real results.
            </Typography>
            <Typography sx={{ color: 'rgba(226,232,240,0.7)', lineHeight: 1.8 }}>
              From custom software development to advanced AI implementations, we partner with
              organizations to transform their operations, enhance customer experiences, and unlock
              new opportunities for growth.
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Grid container spacing={3}>
              {stats.map((stat, index) => (
                <Grid key={stat.label} size={{ xs: 6 }}>
                  <Box sx={{
                    p: 4,
                    background: 'rgba(19, 34, 56, 0.8)',
                    border: '1px solid rgba(100, 180, 255, 0.15)',
                    borderRadius: 2,
                    textAlign: 'center',
                    animation: `${countUp} 0.6s ease-out ${index * 0.1}s both`,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      borderColor: 'rgba(100, 180, 255, 0.3)',
                      transform: 'translateY(-3px)',
                      boxShadow: '0 8px 25px rgba(11, 20, 38, 0.5)',
                    },
                  }}>
                    <Typography variant="h3" sx={{
                      fontWeight: 700,
                      color: '#64B4FF',
                    }}>
                      {stat.number}
                    </Typography>
                    <Typography sx={{ color: 'rgba(226,232,240,0.6)', mt: 1, fontSize: '0.9rem' }}>
                      {stat.label}
                    </Typography>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default About;

