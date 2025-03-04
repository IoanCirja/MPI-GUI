#include <stdio.h>
#include "mpi.h"

int main(int argc, char** argv)
{
     //pornesc MPI
    MPI_Init(&argc, &argv);

    int a, b; //numerle pe care le are fiecare proces
    int rank, size, n;
    int tag = 99;
    
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    MPI_Status status;

    n = size/2;
    //procesul de reducere incepe prin -> frunzele trimit catre parinti
    if( rank >= n){ //proces frunza
        int A[] = {3, 2, 1, 6, 5, 4, 2, 9};
        a = A[rank - n];
        //trimite val "a" la parinte
        MPI_Send(&a, 1, MPI_INT, rank/2 , tag, MPI_COMM_WORLD);
         
    }
    else
    {
        //se asteapta o valoare de la fii, face suma si trimite la parinte
        int suma, a_stanga, a_dreapta;
        //primeste valorile a_stanga si a_dreapta de la procesele fiu: 2*rank si 2*rank+1
        MPI_Recv(&a_stanga, 1, MPI_INT, 2*rank, tag, MPI_COMM_WORLD, &status);
        MPI_Recv(&a_dreapta, 1, MPI_INT, 2*rank+1, tag, MPI_COMM_WORLD, &status);
        a = a_stanga + a_dreapta;
        if(rank > 1){
            //trimite suma la procesul parinte: rank/2
            MPI_Send(&a, 1, MPI_INT, rank/2 , tag, MPI_COMM_WORLD);
        }
        else
        {
            b = a;
            //printeaza valoarea sumei
            printf("A[1] = %d", a);
        }
        
    }

    //procesul de scanare -> frunza trimite valoarea din b catre fii

    if(rank == 1){ //proces radacina
        //trimite b la procesele fiu: 2*rank si 2*rank+1
        MPI_Send(&b, 1, MPI_INT, 2*rank , tag, MPI_COMM_WORLD);
        MPI_Send(&b, 1, MPI_INT, 2*rank+1 , tag, MPI_COMM_WORLD);
    }
    else{
        int b_parinte;
        //primeste b_parinte de la procesul parinte: rank/2
        MPI_Recv(&b_parinte, 1, MPI_INT, rank/2, tag, MPI_COMM_WORLD, &status);
        if(rank % 2 == 1){ //fiu dreapta
            b = b_parinte;
            //trimite val "a" la vecinul din stanga: rank-1
            MPI_Send(&a, 1, MPI_INT, rank-1 , tag, MPI_COMM_WORLD);
        }
        else{
            int a_vecin;
            //primeste a_vecin de la vecinul din drepata: rank+1
            MPI_Recv(&a_vecin, 1, MPI_INT, rank+1, tag, MPI_COMM_WORLD, &status);
            b = b_parinte - a_vecin;
        }

        if(rank < n){ //nod interior
            //trimite b la procesele fiu: 2*rank si 2*rank+1
            MPI_Send(&b, 1, MPI_INT, 2*rank , tag, MPI_COMM_WORLD);
            MPI_Send(&b, 1, MPI_INT, 2*rank+1 , tag, MPI_COMM_WORLD);
        }
        else{
            //printeaza b -> rezultatul scanarii
            printf("Rezultat scanare: %d", b);
        }
    }

    //opresc  MPI
    MPI_Finalize();

    return 0;
}