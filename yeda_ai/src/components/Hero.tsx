import { Box, Container, Typography, Button } from '@mui/material';
import { keyframes } from '@mui/system';

const floatAnimation = keyframes`
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-15px); }
`;

const rotateGradient = keyframes`
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
`;

const Hero = () => {
  return (
    <Box id="home" sx={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      position: 'relative',
      overflow: 'hidden',
      background: 'linear-gradient(135deg, #0B1426 0%, #132238 50%, #0B1426 100%)',
    }}>
      {/* Subtle background elements */}
      <Box sx={{
        position: 'absolute', top: '10%', left: '10%',
        width: 400, height: 400,
        background: 'radial-gradient(circle, rgba(100,180,255,0.08) 0%, transparent 70%)',
        borderRadius: '50%',
        animation: `${floatAnimation} 8s ease-in-out infinite`,
      }} />
      <Box sx={{
        position: 'absolute', bottom: '20%', right: '15%',
        width: 500, height: 500,
        background: 'radial-gradient(circle, rgba(59,130,246,0.06) 0%, transparent 70%)',
        borderRadius: '50%',
        animation: `${floatAnimation} 10s ease-in-out infinite 1s`,
      }} />
      <Box sx={{
        position: 'absolute', top: '50%', left: '60%',
        width: 300, height: 300,
        background: 'radial-gradient(circle, rgba(34,197,94,0.05) 0%, transparent 70%)',
        borderRadius: '50%',
        animation: `${floatAnimation} 12s ease-in-out infinite 2s`,
      }} />
      <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="overline" sx={{
            color: '#64B4FF',
            letterSpacing: 4,
            fontSize: '0.9rem',
            fontWeight: 500,
          }}>
            Enterprise Solutions
          </Typography>
          <Typography variant="h1" sx={{
            fontSize: { xs: '2.5rem', md: '4rem' },
            fontWeight: 700,
            background: 'linear-gradient(90deg, #E2E8F0, #64B4FF, #E2E8F0)',
            backgroundSize: '200% 200%',
            animation: `${rotateGradient} 8s ease infinite`,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            mb: 3,
            letterSpacing: '-1px',
          }}>
            Software, Data & AI Solutions
          </Typography>
          <Typography variant="h6" sx={{
            color: 'rgba(226,232,240,0.7)',
            maxWidth: 650,
            mx: 'auto',
            mb: 5,
            lineHeight: 1.8,
            fontWeight: 400,
          }}>
            Transform your business with cutting-edge technology. We deliver intelligent solutions that drive growth and innovation.
          </Typography>
          <Box sx={{ display: 'flex', gap: 3, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button variant="contained" size="large" onClick={() => document.getElementById('services')?.scrollIntoView({ behavior: 'smooth' })} sx={{
              background: 'linear-gradient(135deg, #3B82F6, #1E40AF)',
              px: 5, py: 1.5,
              fontSize: '1rem',
              borderRadius: '8px',
              boxShadow: '0 4px 15px rgba(59, 130, 246, 0.3)',
              '&:hover': {
                transform: 'translateY(-2px)',
                boxShadow: '0 6px 20px rgba(59, 130, 246, 0.4)',
                background: 'linear-gradient(135deg, #3B82F6, #1E40AF)',
              },
            }}>
              Explore Services
            </Button>
            <Button variant="outlined" size="large" onClick={() => document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' })} sx={{
              borderColor: 'rgba(100, 180, 255, 0.5)',
              color: '#64B4FF',
              px: 5, py: 1.5,
              fontSize: '1rem',
              borderRadius: '8px',
              '&:hover': {
                borderColor: '#64B4FF',
                backgroundColor: 'rgba(100, 180, 255, 0.1)',
                transform: 'translateY(-2px)',
              },
            }}>
              Get in Touch
            </Button>
          </Box>
        </Box>
      </Container>
    </Box>
  );
};

export default Hero;

